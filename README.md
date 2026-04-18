# Free Fire UID Verification API — APEX v3.0

Production-ready API and CLI for fetching Free Fire player data across all 14 Garena regions. Optimized for OB53 (April 2026).

## Features

- **All 14 Regions Supported**: IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA.
- **Deep Data Extraction**: Account info, ranks, detailed stats (Solo/Duo/Squad), guild info, pet details, cosmetics, and ban status.
- **Production Architecture**:
    - Asynchronous I/O with `aiohttp` and `FastAPI`.
    - JWT authentication lifecycle management with auto-refresh.
    - AES-CBC encrypted wire protocol handling.
    - Dual Protobuf strategy (Compiled vs. Raw Binary fallback).
    - TTL Cache with LRU eviction and cache stampede protection.
    - Comprehensive Pydantic v2 schemas.
    - Rate limiting and request tracking.
- **Interfaces**: REST API (FastAPI) and CLI (argparse).

## Installation

### Standard Setup
```bash
git clone https://github.com/your-repo/ff-api.git
cd ff-api
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### Termux (Android)
```bash
pkg install python rust binutils
pip install -r requirements.txt
```

## Configuration (.env)

| Variable | Description |
|----------|-------------|
| `GARENA_GUEST_UID` | Guest account UID for authentication |
| `GARENA_GUEST_TOKEN` | Guest account token |
| `AES_KEY` | 32-byte hex key for payload encryption |
| `AES_IV` | 16-byte hex IV |
| `OB_VERSION` | Current Garena version (e.g., OB53) |

### Obtaining Credentials
1. Install Free Fire on an emulator/device.
2. Use a packet sniffer (e.g., HttpCanary or PCAPdroid) or Frida.
3. Capture the request to `loginbp.ggblueshark.com/MajorLogin`.
4. Extract the `uid` and `token` from the request body.

## Usage

### REST API
Start the server:
```bash
python main.py --serve --port 8080
```

Endpoints:
- `GET /player?uid=4899748638&region=IND`
- `GET /batch?uids=4899748638,12345678&region=IND`
- `GET /regions`
- `GET /health`

### CLI
```bash
# Fetch single player
python cli.py --uid 4899748638 --region IND

# Batch fetch from file
python cli.py --batch uids.txt --region IND --format compact
```

## Testing
```bash
pytest
```

## Legal Disclaimer
This project is for educational purposes only. It is not affiliated with or endorsed by Garena.
