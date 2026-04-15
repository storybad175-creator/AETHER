# Free Fire UID Verification API — APEX v3.0

The gold standard API for fetching publicly accessible data for any Free Fire player across all 14 regions.

## Features
- **All 14 Regions**: IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA.
- **Full Data Schema**: Account info, ranks, stats (Solo/Duo/Squad), guild, pet, cosmetics, and ban status.
- **Dual Interface**: FastAPI web server and argparse CLI.
- **Robust Pipeline**: AES-CBC encryption, Protobuf v3 serialization, JWT auto-refresh, and TTL caching.
- **Production Ready**: Rate limiting, retry-backoff, error handling, and Pydantic v2 schemas.

## Installation

```bash
git clone https://github.com/your-repo/ff-api.git
cd ff-api
pip install -r requirements.txt
```

### Termux (Android)
```bash
pkg update && pkg upgrade
pkg install python git
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`.
2. Update the following variables:
   - `GARENA_GUEST_UID` & `GARENA_GUEST_TOKEN`: Extracted from a guest login.
   - `AES_KEY` & `AES_IV`: Extracted from the APK binary (OB53).

### Guest JWT Extraction Guide
Use Frida or a proxy like Burp Suite to capture the request to `https://loginbp.ggblueshark.com/MajorLogin` when logging in as a guest in the Free Fire app.

## Usage

### CLI
```bash
python cli.py --uid 4899748638 --region IND
python cli.py --batch uids.txt --region BR
```

### Server
```bash
python main.py --serve --port 8080
```

### API Endpoints
- `GET /player?uid={uid}&region={region}`
- `GET /batch?uids={u1,u2}&region={region}`
- `GET /regions`
- `GET /health`

## Updating for New OB Versions
When Garena releases a new update (e.g., OB54), simply update the `OB_VERSION` in your `.env` file. If AES keys rotate, update `AES_KEY` and `AES_IV` as well.
