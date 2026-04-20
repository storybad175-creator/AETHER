# Free Fire UID Verification API — APEX v3.0 UNLIMITED

A high-performance, asynchronous Python API and CLI for fetching comprehensive player data across all 14 Garena regions. Optimized for OB53 (April 2026).

## Features

- **All 14 Regions Supported**: IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA.
- **Deep Data Retrieval**: Account info, BR/CS ranks, detailed stats (Solo/Duo/Squad), Guild info, Pet details, equipped cosmetics, and ban status.
- **Robust Architecture**:
  - AES-CBC payload encryption/decryption with key rotation detection.
  - Dual Protobuf strategy (Compiled / Raw Binary recursive fallback).
  - JWT lifecycle management with auto-refresh and proactive expiry.
  - TTL In-memory cache with LRU-ish eviction and per-key locking.
  - Exponential backoff and retry logic (1s, 3s, 7s).
- **Dual Interface**: FastAPI web server and a powerful colorized CLI.

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

1. **Garena Guest Credentials**:
   - Open Free Fire.
   - Use Frida or a proxy (like Burp/Proxyman) to capture the `MajorLogin` request to `https://loginbp.ggblueshark.com/MajorLogin`.
   - Extract `uid` and `token` from the JSON body.
   - Set `GARENA_GUEST_UID` and `GARENA_GUEST_TOKEN` in `.env`.

2. **AES Constants**:
   - Key and IV are extracted from the APK's native libraries (`libil2cpp.so` or `libunity.so`).
   - Search for the wire protocol encryption block.
   - Set `AES_KEY` (32-byte hex) and `AES_IV` (16-byte hex) in `.env`.

3. **OB Version**:
   - Update `OB_VERSION` in `.env` (e.g., `OB53`, `OB54`) when a new game update is released. No code changes required.

## Usage

### Web Server
```bash
python main.py --serve --port 8080
```
Endpoints:
- `GET /player?uid={uid}&region={region}`
- `GET /batch?uids={u1,u2}&region={region}` (Max 10 concurrent)
- `GET /health`
- `GET /regions`

### CLI
```bash
# Single lookup (Pretty printed & Colorized)
python cli.py --uid 123456789 --region IND

# Batch lookup from file
python cli.py --batch uids.txt --region SG

# Compact JSON output
python cli.py --uid 123456789 --region IND --format compact

# List regions
python cli.py --regions
```

## Testing
```bash
pytest
```

## Disclaimer
This project is for educational and research purposes only. Use responsibly and respect Garena's Terms of Service.
