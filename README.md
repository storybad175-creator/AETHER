# Free Fire UID Verification API — APEX v3.0 UNLIMITED

A high-performance, asynchronous Python API and CLI for fetching comprehensive player data across all 14 Garena regions. Optimized for OB53 (April 2026).

## Features

- **All 14 Regions Supported**: IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA.
- **Deep Data Retrieval**: Account info, BR/CS ranks, detailed stats (Solo/Duo/Squad), Guild info, Pet details, equipped cosmetics, and ban status.
- **Robust Architecture**:
  - AES-CBC payload encryption/decryption.
  - Dual Protobuf strategy (Compiled / Raw Binary fallback).
  - JWT lifecycle management with auto-refresh.
  - TTL In-memory cache with LRU eviction.
  - Exponential backoff and retry logic.
- **Dual Interface**: FastAPI web server and a powerful CLI.

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

1. **Garena Guest Credentials**: Use Frida or a proxy (like Burp/Proxyman) to capture the `MajorLogin` request from the Free Fire app to get your guest UID and Token.
   - **Methodology**:
     - Open Free Fire.
     - Capture traffic to `https://loginbp.ggblueshark.com/MajorLogin`.
     - Extract `uid` and `token` from the JSON request body.
2. **AES Constants**: Key and IV are extracted from the APK's native libraries (`libil2cpp.so` or `libunity.so`).
   - **Methodology**:
     - Use `grep` or `strings` on the unpacked `.so` files to find 32-byte hex strings.
     - Look for function calls involving AES or encryption initialization.
3. **OB Version**: Update `OB_VERSION` in `.env` when a new game update is released (e.g., `OB54`).

## Usage

### Web Server
```bash
python main.py --port 8080
```
Endpoints:
- `GET /player?uid={uid}&region={region}`: Single player lookup.
- `GET /batch?uids={u1,u2}&region={region}`: Concurrently fetch up to 10 players.
- `GET /health`: Check system status and version.
- `GET /regions`: List all supported region codes.

### CLI
```bash
# Single lookup (Pretty print)
python cli.py --uid 123456789 --region IND

# Single lookup (Compact JSON)
python cli.py --uid 123456789 --region IND --format compact

# Batch lookup from file (Concurrently processes UIDs)
python cli.py --batch uids.txt --region SG

# List regions
python cli.py --regions

# Check health
python cli.py --health
```

## Testing
Run the comprehensive test suite to ensure system integrity:
```bash
python3 -m pytest
```

## Disclaimer
This project is for educational and research purposes only. Use responsibly and respect Garena's Terms of Service.
