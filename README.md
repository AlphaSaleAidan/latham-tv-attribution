# Latham Pools TV Attribution Platform

Correlate TV commercial airings with digital lead generation signals to answer: **"How is TV positively impacting the Latham Pools business?"**

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
│  TV Airing   │────▶│   Correlation    │────▶│    Reports &   │
│  Data (CSV)  │     │     Engine       │     │   Dashboards   │
└──────────────┘     │                  │     └────────────────┘
                     │  Time-window     │
┌──────────────┐     │  analysis:       │     ┌────────────────┐
│ Google Trends│────▶│  0-30min         │────▶│  PDF Reports   │
│ (pytrends)   │     │  0-2hr           │     └────────────────┘
└──────────────┘     │  0-24hr          │
                     │  0-72hr          │
┌──────────────┐     │                  │
│   GA4 API    │────▶│  DMA-level geo   │
│   + Search   │     │  matching vs     │
│   Console    │     │  7-day baseline  │
└──────────────┘     └──────────────────┘
```

## Stack

- **API**: Python / FastAPI
- **Database**: Supabase (PostgreSQL)
- **Hosting**: Railway
- **Data Sources**: Google Trends, GA4, Search Console, CallRail, QR codes, SEMrush

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the API
uvicorn app.main:app --reload --port 8000
```

## Data Sources

| Source | Signal Type | Latency | Cost |
|--------|-----------|---------|------|
| TV Airing CSV | Trigger event | Manual upload | Free |
| Google Trends (pytrends) | Brand lift | ~30 min | Free |
| GA4 Data API | Web traffic + conversions | 24-48hr | Free |
| GA4 Realtime API | Immediate web traffic | Real-time | Free |
| Google Search Console | Organic search performance | 2-3 days | Free |
| CallRail | Phone call attribution | Real-time | $45/mo+ |
| QR Codes (Flowcode/Bitly) | Direct scan attribution | Real-time | Free tier |
| SEMrush | SEO rankings | Daily | $130/mo+ |

## Project Structure

```
app/
├── main.py              # FastAPI application entry
├── api/                 # API route handlers
│   ├── airings.py       # TV airing CRUD + CSV upload
│   ├── trends.py        # Google Trends endpoints
│   ├── analytics.py     # GA4 integration
│   ├── correlation.py   # Correlation analysis endpoints
│   └── reports.py       # Report generation
├── core/                # Configuration & utilities
│   ├── config.py        # Environment config
│   ├── database.py      # Supabase connection
│   └── dependencies.py  # FastAPI dependencies
├── etl/                 # Data extraction & transformation
│   ├── trends.py        # Google Trends ETL
│   ├── ga4.py           # GA4 data extraction
│   ├── search_console.py
│   └── callrail.py
├── models/              # Pydantic models & DB schemas
│   ├── airing.py
│   ├── trend.py
│   ├── analytics.py
│   └── correlation.py
├── services/            # Business logic
│   ├── correlation.py   # Time-window correlation engine
│   ├── baseline.py      # 7-day rolling baseline calc
│   └── geo_matching.py  # DMA-level geographic matching
tests/
scripts/
docs/
```

## Correlation Methodology

1. **Time-window analysis**: For each TV airing, measure digital signal changes across 4 windows (0-30min, 0-2hr, 0-24hr, 0-72hr)
2. **Baseline comparison**: Compare post-airing signals against a 7-day rolling baseline for the same DMA/time-of-day
3. **Adstock modeling**: Apply exponential decay to model how TV ad effects diminish over time (borrowed from Google LightweightMMM)
4. **Geo matching**: Match TV airing DMAs to digital signal geography for attribution confidence scoring
5. **Statistical significance**: Flag correlations that exceed 2σ above baseline as "likely TV-driven"

## License

Private — AlphaSale / Latham Pools
