# Free Fire UID Verification API — APEX v3.0 UNLIMITED

A high-performance, asynchronous Python API and CLI for fetching comprehensive player data across all 14 Garena regions. Optimized for OB53 (April 2026).

## Features

- **All 14 Regions Supported**: IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA.
- **Deep Data Retrieval**: Account info, BR/CS ranks, detailed stats (Solo/Duo/Squad), Guild info, Pet details, cosmetics, and ban status.
- **Robust Architecture**:
  - AES-CBC payload encryption/decryption (Reverse-engineered constants).
  - Recursive Protobuf Strategy B (Raw binary decoding for unknown schemas).
  - JWT lifecycle management with proactive auto-refresh.
  - TTL In-memory cache with LRU-ish eviction and lock-per-key.
  - Exponential backoff and automated retry for 429/401/5xx errors.
- **Dual Interface**: FastAPI web server and a colorized CLI.

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
pkg update && pkg upgrade
pkg install python rust binutils
pip install -r requirements.txt
```

## Configuration (.env)

1. **Garena Guest Credentials**: Use Frida or a proxy to capture the `MajorLogin` request (`https://loginbp.ggblueshark.com/MajorLogin`) from the Free Fire app.
2. **AES Constants**: Key and IV are extracted from `libil2cpp.so` or `libunity.so` in the APK. They must be 64-char and 32-char hex strings respectively.
3. **OB Version**: Set `OB_VERSION=OB53` in `.env`.

## Usage

### Web Server
```bash
python main.py --port 8080
```
- `GET /player?uid={uid}&region={region}`
- `GET /batch?uids={u1,u2}&region={region}`
- `GET /health`
- `GET /regions`

### CLI
```bash
# Single lookup
python cli.py --uid 123456789 --region IND

# Batch lookup from file (concurrently)
python cli.py --batch uids.txt --region SG

# Help
python cli.py --help
```

## Testing
```bash
python3 -m pytest
```

## Architecture
- `api/`: FastAPI routes, schemas (Pydantic v2), and middleware.
- `config/`: Global settings and protocol mappings (Regions, Ranks, Fields).
- `core/`: Core logic for auth, crypto, protobuf, transport, and caching.
- `proto/`: Protobuf definition files and minimal compiled stubs.

## Disclaimer
This project is for educational and research purposes only. Use responsibly and respect Garena's Terms of Service.
