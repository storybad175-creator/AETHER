# Free Fire UID Verification API — APEX v3.0 UNLIMITED

The definitive, production-ready implementation for fetching comprehensive Free Fire player data across all 14 Garena regions. Optimized for **OB53 (April 2026)**.

## 🚀 Features

- **Global Coverage**: Supports IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, and NA.
- **Detailed Data**: Fetches account info, BR/CS ranks, detailed stats (Solo/Duo/Squad), Guild info, Pet details, equipped cosmetics, and ban status.
- **Enterprise Architecture**:
  - **AES-CBC** payload encryption/decryption.
  - **Recursive Protobuf** Strategy B decoder (no .proto required).
  - **JWT Lifecycle** manager with proactive auto-refresh.
  - **TTL Cache** with LRU eviction and cache stampede protection.
  - **Exponential Backoff** retry logic for high reliability.
- **Dual Interface**: Full FastAPI web server and a feature-rich CLI.

## 🛠️ Installation

### Standard Setup
```bash
git clone https://github.com/your-repo/ff-api.git
cd ff-api
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your specific credentials
```

### Termux (Android)
```bash
pkg update && pkg upgrade
pkg install python rust binutils
pip install -r requirements.txt
cp .env.example .env
```

## ⚙️ Configuration (.env)

1.  **Garena Guest Credentials**: Use a proxy (Burp Suite, Proxyman) or Frida to capture the `MajorLogin` request from the Free Fire app.
2.  **AES Constants**: Key and IV are extracted from the APK's `libil2cpp.so`. Check community forums for the latest Hex values for the current OB version.
3.  **OB Version**: Update `OB_VERSION` in `.env` whenever a new game update drops.

## 🖥️ Usage

### Web Server (FastAPI)
```bash
python main.py
```
- **GET** `/player?uid={uid}&region={region}`: Fetch single player.
- **GET** `/batch?uids={u1,u2}&region={region}`: Concurrent fetch for up to 10 UIDs.
- **GET** `/health`: Check API status and version.
- **GET** `/regions`: List all 14 supported regions.

### CLI (argparse)
```bash
# Single Lookup
python cli.py --uid 123456789 --region IND

# Batch Lookup from File
python cli.py --batch uids.txt --region SG --format compact

# Health & Version Check
python cli.py --health
```

## 🧪 Testing
Run the comprehensive test suite with:
```bash
pytest
```

## ⚠️ Disclaimer
This project is for educational and research purposes only. Use responsibly and respect Garena's Terms of Service.
