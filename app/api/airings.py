"""TV airing endpoints — CRUD and CSV upload."""

import csv
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from supabase import Client

from app.core.dependencies import get_db
from app.models.airing import Airing, AiringCreate, AiringCSVUpload, AiringFilter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/airings", tags=["TV Airings"])


# Common CSV column mappings (flexible header matching)
COLUMN_ALIASES = {
    "airing_timestamp": ["airing_timestamp", "timestamp", "air_date", "air_time", "date_time", "datetime", "air_datetime"],
    "network": ["network", "channel", "station", "net"],
    "dma_code": ["dma_code", "dma", "dma_id", "market_code"],
    "dma_name": ["dma_name", "market", "market_name", "dma_market"],
    "creative_id": ["creative_id", "isci", "isci_code", "ad_id", "spot_id", "creative"],
    "creative_name": ["creative_name", "ad_name", "spot_name", "title"],
    "duration_seconds": ["duration_seconds", "duration", "length", "spot_length", "dur"],
    "estimated_impressions": ["estimated_impressions", "impressions", "imps", "est_impressions"],
    "spend": ["spend", "cost", "rate", "amount", "price"],
    "daypart": ["daypart", "day_part"],
    "program_name": ["program_name", "program", "show", "show_name"],
}


def _match_column(header: str, aliases: dict) -> Optional[str]:
    """Match a CSV header to a known field using aliases."""
    header_lower = header.strip().lower().replace(" ", "_").replace("-", "_")
    for field, alias_list in aliases.items():
        if header_lower in alias_list:
            return field
    return None


@router.post("/upload-csv", response_model=AiringCSVUpload)
async def upload_airings_csv(
    file: UploadFile = File(...),
    db: Client = Depends(get_db),
):
    """Upload a CSV of TV airings. Flexible column matching."""

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    text = content.decode("utf-8-sig")  # Handle BOM
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV has no headers")

    # Map CSV columns to our fields
    column_map = {}
    for header in reader.fieldnames:
        matched = _match_column(header, COLUMN_ALIASES)
        if matched:
            column_map[header] = matched

    if "airing_timestamp" not in column_map.values():
        raise HTTPException(
            status_code=400,
            detail=f"CSV must have a timestamp column. Found headers: {reader.fieldnames}. "
            f"Expected one of: {COLUMN_ALIASES['airing_timestamp']}",
        )

    rows_imported = 0
    rows_skipped = 0
    errors = []
    sample_records = []

    for i, row in enumerate(reader):
        try:
            record = {}
            for csv_col, our_field in column_map.items():
                val = row.get(csv_col, "").strip()
                if val:
                    if our_field == "airing_timestamp":
                        # Try multiple date formats
                        for fmt in [
                            "%Y-%m-%d %H:%M:%S",
                            "%Y-%m-%dT%H:%M:%S",
                            "%Y-%m-%dT%H:%M:%SZ",
                            "%m/%d/%Y %H:%M:%S",
                            "%m/%d/%Y %H:%M",
                            "%m/%d/%Y %I:%M %p",
                            "%m/%d/%y %H:%M:%S",
                        ]:
                            try:
                                record[our_field] = datetime.strptime(val, fmt).replace(
                                    tzinfo=timezone.utc
                                ).isoformat()
                                break
                            except ValueError:
                                continue
                        else:
                            errors.append(f"Row {i+1}: Could not parse timestamp '{val}'")
                            rows_skipped += 1
                            continue
                    elif our_field in ("duration_seconds", "estimated_impressions"):
                        record[our_field] = int(float(val.replace(",", "")))
                    elif our_field == "spend":
                        record[our_field] = float(val.replace(",", "").replace("$", ""))
                    else:
                        record[our_field] = val

            if "airing_timestamp" not in record:
                rows_skipped += 1
                continue

            record["id"] = str(uuid.uuid4())
            record["created_at"] = datetime.now(timezone.utc).isoformat()
            record["updated_at"] = record["created_at"]

            # Insert into Supabase
            db.table("tv_airings").insert(record).execute()
            rows_imported += 1

            if len(sample_records) < 3:
                sample_records.append(record)

        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)[:100]}")
            rows_skipped += 1

    return AiringCSVUpload(
        rows_imported=rows_imported,
        rows_skipped=rows_skipped,
        errors=errors[:20],  # Cap error list
        sample_records=sample_records,
    )


@router.get("/")
async def list_airings(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    network: Optional[str] = None,
    dma_code: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: Client = Depends(get_db),
):
    """List TV airings with optional filters."""
    query = db.table("tv_airings").select("*")

    if start_date:
        query = query.gte("airing_timestamp", start_date.isoformat())
    if end_date:
        query = query.lte("airing_timestamp", end_date.isoformat())
    if network:
        query = query.eq("network", network)
    if dma_code:
        query = query.eq("dma_code", dma_code)

    query = query.order("airing_timestamp", desc=True).range(offset, offset + limit - 1)
    result = query.execute()

    return {"data": result.data, "count": len(result.data)}


@router.get("/{airing_id}")
async def get_airing(airing_id: str, db: Client = Depends(get_db)):
    """Get a single airing by ID."""
    result = db.table("tv_airings").select("*").eq("id", airing_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Airing not found")
    return result.data[0]


@router.post("/")
async def create_airing(airing: AiringCreate, db: Client = Depends(get_db)):
    """Create a single TV airing record."""
    record = airing.model_dump()
    record["id"] = str(uuid.uuid4())
    record["airing_timestamp"] = record["airing_timestamp"].isoformat()
    record["created_at"] = datetime.now(timezone.utc).isoformat()
    record["updated_at"] = record["created_at"]

    result = db.table("tv_airings").insert(record).execute()
    return result.data[0] if result.data else record
