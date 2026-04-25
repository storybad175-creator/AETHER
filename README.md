# Free Fire UID Verification API — APEX v3.0 UNLIMITED

A high-performance, asynchronous Python API and CLI for fetching comprehensive player data across all 14 Garena regions. Optimized for OB53 (April 2026).

## Features

- **All 14 Regions Supported**: IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA.
- **Deep Data Retrieval**: Account info, BR/CS ranks, detailed stats (Solo/Duo/Squad), Guild info, Pet details, equipped cosmetics, and ban status.
- **Robust Architecture**:
  - AES-CBC payload encryption/decryption with auto-rotation detection.
  - Dual Protobuf strategy (Compiled / Raw Binary fallback).
  - JWT lifecycle management with auto-refresh.
  - TTL In-memory cache with LRU eviction and cache stampede prevention.
  - Exponential backoff and retry logic.
  - Automatic port conflict resolution for the web server.
- **Dual Interface**: FastAPI web server and a powerful CLI.

## Installation

### Standard Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/ff-api.git
   cd ff-api
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (see Configuration section below)
   ```

### Termux (Android)
```bash
pkg update && pkg upgrade
pkg install python rust binutils
pip install -r requirements.txt
```

## Configuration (.env)

The API requires several keys and credentials to function correctly:

### 1. Garena Guest Credentials
Garena uses JWT for authentication. You must obtain a guest `UID` and `TOKEN` from the `MajorLogin` endpoint.
- **Methodology**: Use a tool like Frida, Burp Suite, or Proxyman on an Android emulator or rooted device to capture the HTTPS POST request to `https://loginbp.ggblueshark.com/MajorLogin` when the Free Fire app starts.
- **Fields**: Extract `uid` and `token` from the request body and set them as `GARENA_GUEST_UID` and `GARENA_GUEST_TOKEN` in your `.env`.

### 2. AES Constants
The wire protocol uses AES-CBC encryption. The keys rotate with game updates (OB versions).
- **Methodology**: These are found in the native C++ libraries of the APK (`libil2cpp.so`).
- **Fields**: `AES_KEY` (32-byte hex) and `AES_IV` (16-byte hex).
- **Rotation**: If you see "PROTOBUF DECODE FAILURE" in logs, it likely means Garena has rotated the keys. Check community forums (hlgamingofficial.com, etc.) for the latest constants.

### 3. OB Version
Set `OB_VERSION` to the current game version (e.g., `OB53`). This is used in the `X-Garena-OB` header.

## Usage

### Web Server
Start the FastAPI server:
```bash
python main.py --port 8080
```
If port 8080 is occupied, the server will automatically try 8081, 8082, etc.

**Endpoints:**
- `GET /player?uid={uid}&region={region}`: Fetch full player profile.
- `GET /batch?uids={u1,u2}&region={region}`: Fetch multiple profiles (up to 10) concurrently.
- `GET /health`: Check system status and version.
- `GET /regions`: List all 14 supported region codes.

### CLI
The command-line interface supports single and batch lookups.
```bash
# Single lookup
python cli.py --uid 123456789 --region IND

# Compact output (single-line JSON)
python cli.py --uid 123456789 --region IND --format compact

# Batch lookup from file (one UID per line)
python cli.py --batch uids.txt --region SG

# Health and Regions
python cli.py --health
python cli.py --regions
```

## Testing
Run the comprehensive test suite to verify your setup:
```bash
python3 -m pytest
```

## Failure Mode Recovery
The system is designed to handle various failure scenarios:
- **FM-01 (JWT Expiry)**: Automatically refreshes token on 401 response.
- **FM-02 (Wrong Region)**: 404 errors include suggestions for common regions.
- **FM-04 (Key Rotation)**: Explicitly identifies decryption-but-decode failures and warns the user to update keys.
- **FM-09 (Port Conflict)**: Automatically hunts for an available port on startup.
- **FM-11 (Cache Stampede)**: Uses per-key locks to ensure only one network request is made for concurrent identical lookups.

## Disclaimer
This project is for educational and research purposes only. APEX v3.0 is a reverse-engineering demonstration. Use responsibly and respect Garena's Terms of Service.
