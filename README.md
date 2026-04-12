# Free Fire UID Verification API — APEX v3.0 Unlimited

A production-ready, high-performance Python API for fetching comprehensive Free Fire player data across all 14 global regions.

## Features

- **Multi-Region Support**: All 14 Garena regions (IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA).
- **Advanced Pipeline**: Full Protobuf binary serialization/deserialization with AES-CBC encryption.
- **Smart Auth**: Automated JWT lifecycle management for Garena guest accounts.
- **High Performance**: Built with `FastAPI` and `aiohttp` for asynchronous, non-blocking I/O.
- **Reliability**: Exponential backoff retries, proactive token refresh, and circuit-breaker ready.
- **Caching**: TTL-based in-memory cache with LRU eviction and concurrency protection.
- **Dual Interface**: Full FastAPI web server and a powerful CLI tool.
- **Type Safety**: Pydantic v2 models for strict input validation and structured output.

## Installation

### Prerequisites
- Python 3.8 or higher
- `pip` or `conda`

### Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your real Garena credentials and AES keys
   ```

### Termux (Android)
```bash
pkg install python rust
pip install -r requirements.txt
```

## Configuration (.env)

| Variable | Description |
|----------|-------------|
| `GARENA_GUEST_UID` | Your Garena guest account UID. |
| `GARENA_GUEST_TOKEN` | Your Garena guest account login token. |
| `AES_KEY` | 32-byte hex-encoded AES key for Garena protocol. |
| `AES_IV` | 16-byte hex-encoded AES IV for Garena protocol. |
| `OB_VERSION` | Current Garena OB version (e.g., OB53). |

## Usage

### CLI
```bash
# Fetch a single player
python cli.py --uid 4899748638 --region IND

# Batch process UIDs from a file
python cli.py --batch uids.txt --region IND

# Start the web server via CLI
python cli.py --serve --port 8080
```

### FastAPI Web Server
```bash
python main.py
```
- **GET** `/player?uid={uid}&region={region}`: Fetch player profile.
- **GET** `/batch?uids={u1,u2}&region={region}`: Concurrent fetch for up to 10 UIDs.
- **GET** `/health`: System status and version info.
- **GET** `/regions`: List all supported region codes.

## Testing
Run the comprehensive test suite with:
```bash
pytest
```

## Credits
Reverse-engineered from Garena Free Fire internal protocols (OB53, April 2026). This tool is for educational purposes only.
