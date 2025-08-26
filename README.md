# Aviation Standing Data API

A FastAPI-based REST API service for querying aviation standing data including aircraft, airlines, airports, and routes. This service reads CSV data files from the Virtual Radar Server community and provides fast lookups with a web interface.

## 🔄 Auto-Sync with Upstream

This repository is a **fork** of [vradarserver/standing-data](https://github.com/vradarserver/standing-data) with added API functionality. 

**Automatic Updates:** This fork automatically syncs with the original repository **daily at 06:00 UTC** via GitHub Actions. The aviation data stays up-to-date while preserving the API enhancements.

- **Original Data Source**: [vradarserver/standing-data](https://github.com/vradarserver/standing-data)
- **Sync Schedule**: Daily at 06:00 UTC
- **Manual Sync**: Can be triggered anytime from the Actions tab
- **Data Preservation**: Your API additions remain intact during syncs

## Features

- 🛩️ **Aircraft Search** - Search by ICAO, registration, or operator
- ✈️ **Airport Lookup** - Find airports by code, name, or country
- 🛫 **Airline Database** - Browse airline information with ICAO/IATA codes
- 🗺️ **Route Information** - Query flight routes and callsigns
- 🌍 **Country Data** - ISO country codes and names
- 🔧 **Model Types** - Aircraft model information with technical specs
- 📊 **Interactive Web UI** - Built-in search interface
- 🐳 **Docker Ready** - Containerized with nginx frontend
- 📝 **OpenAPI Docs** - Automatic API documentation

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and run the services:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Web Interface: http://localhost:30000
   - API Documentation: http://localhost:30000/docs
   - Health Check: http://localhost:30000/health

3. **Stop the services:**
   ```bash
   docker-compose down
   ```

### Manual Setup

1. **Install dependencies:**
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. **Run the FastAPI server:**
   ```bash
   python main.py
   # or
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the application:**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## API Endpoints

### Aircraft
- **GET /aircraft** - Search aircraft
  - Query parameters: `icao`, `registration`, `operator`, `limit` (max 1000)
  - Example: `/aircraft?registration=VP-C&limit=10`

### Airlines
- **GET /airlines** - Get all airlines
  - Returns: List of airlines with ICAO, IATA codes, and names

### Airports
- **GET /airports** - Search airports
  - Query parameters: `code`, `icao`, `iata`, `name`, `country`, `limit` (max 1000)
  - `code`: Search by any airport code (matches ICAO, IATA, or Code field)
  - `icao`: Search by specific ICAO code (e.g. EGLL)
  - `iata`: Search by specific IATA code (e.g. LHR)
  - Examples: 
    - `/airports?icao=EGLL` (find London Heathrow by ICAO)
    - `/airports?iata=LHR` (find London Heathrow by IATA)
    - `/airports?code=LHR` (find any airport matching LHR)
    - `/airports?country=US&limit=50` (US airports)

### Routes
- **GET /routes** - Search flight routes
  - Query parameters: `callsign`, `code`, `airline_code`, `limit` (max 1000)
  - Example: `/routes?airline_code=EZY&limit=20`

### Reference Data
- **GET /countries** - Get all countries (ISO codes)
- **GET /model-types** - Get aircraft model types
- **GET /code-blocks** - Get Mode-S ICAO code blocks with country assignments
- **GET /registration-prefixes** - Get aircraft registration prefix patterns
- **GET /health** - Service health check

## Architecture

### Components
- **FastAPI Application** (`api/main.py`) - REST API server with data loading
- **Nginx Proxy** (`nginx/`) - Frontend reverse proxy with rate limiting
- **Docker Setup** - Multi-container deployment with health checks

### Data Loading Strategy
- **Lazy Loading** - Data loaded on first request and cached
- **Hierarchical Search** - Efficient traversal of CSV file structure
- **Memory Optimization** - Limited directory scanning for performance
- **Error Handling** - Graceful handling of missing or corrupted files

### Performance Features
- **Caching** - In-memory caching of frequently accessed data
- **Rate Limiting** - Nginx-based request throttling (10 req/sec)
- **Gzip Compression** - Automatic response compression
- **Health Checks** - Container health monitoring
- **Result Limits** - Configurable result set sizes

## Configuration

### Environment Variables
- `PYTHONUNBUFFERED=1` - Python stdout/stderr buffering

### Port Configuration
- **NodePort**: 30000 (external access)
- **Internal**: nginx:80 → api:8000
- **Development**: Direct access on port 8000

### Volume Mounts
- Standing data directory mounted read-only at `/data`
- Preserves original file structure and permissions

## Data Schema

The API serves data from CSV files organized in the following structure:

```
aircraft/schema-01/{digit}/{two-digits}/{three-digits}.csv
airlines/schema-01/airlines.csv
airports/schema-01/{letter}/{two-letters}.csv
routes/schema-01/{letter}/{code}-{all|digit}.csv
countries/schema-01/countries.csv
model-type/schema-01/{letter}.csv
code-blocks/schema-01/code-blocks.csv
registration-prefixes/schema-01/reg-prefixes.csv
```

### Sample Queries

**Find aircraft by registration:**
```bash
curl "http://localhost:30000/aircraft?registration=VP-C&limit=5"
```

**Search airports in a country:**
```bash
curl "http://localhost:30000/airports?country=GB&limit=10"
```

**Get airline information:**
```bash
curl "http://localhost:30000/airlines" | jq '.[] | select(.ICAO=="BAW")'
```

**Find routes by airline:**
```bash
curl "http://localhost:30000/routes?airline_code=EZY&limit=5"
```

## Development

### Adding New Endpoints
1. Add endpoint function in `api/main.py`
2. Update the DataLoader class if needed
3. Add corresponding UI elements to the HTML template

### Modifying Search Logic
- Update search methods in the `DataLoader` class
- Implement caching for new data types
- Consider performance impact on large datasets

### Nginx Configuration
- Rate limiting settings in `nginx/nginx.conf`
- Add new routes or modify proxy behavior
- Update health check endpoints

## Monitoring

### Health Checks
- **API**: `/health` - FastAPI service status
- **Nginx**: `/nginx-health` - Proxy service status
- **Docker**: Built-in container health checks

### Logging
- Nginx access logs: `/var/log/nginx/access.log`
- Application logs: Container stdout/stderr
- Error logs: `/var/log/nginx/error.log`

## Security

### Rate Limiting
- 10 requests per second per IP address
- Burst allowance of 20 requests
- Applied to all API endpoints

### Headers
- Security headers for XSS and clickjacking protection
- Content-Type validation
- CORS enabled for development

### Network
- Isolated Docker network (172.20.0.0/16)
- Service-to-service communication only
- Read-only data volume mounts

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
docker-compose logs api
docker-compose logs nginx

# Verify data directory permissions
ls -la /path/to/standing-data/
```

**No data returned:**
```bash
# Verify data mount
docker-compose exec api ls -la /data/

# Check API health
curl http://localhost:30000/health
```

**Performance issues:**
```bash
# Monitor container resources
docker stats

# Check nginx rate limiting
docker-compose logs nginx | grep limit
```

### Development Tips
- Use `--reload` flag for development servers
- Mount code directory for live reloading
- Access FastAPI directly on port 8000 for debugging
- Use `/docs` endpoint for interactive API testing