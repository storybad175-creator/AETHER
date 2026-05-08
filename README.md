# 🎮 Free Fire UID Verification API — APEX v3.0

The definitive, production-ready implementation for fetching complete, publicly accessible player data from Garena Free Fire. Supporting all 14 regions and optimized for **OB53 (April 2026)**.

## 🚀 Features

-   **All 14 Regions:** IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA.
-   **Deep Data:** Profile (Nickname, Level, EXP), Ranks (BR & CS), Stats (Solo, Duo, Squad), Guild, Pet, Cosmetics, and Ban status.
-   **Robust Pipeline:** AES-CBC decryption, recursive Protobuf Strategy B decoding, and JWT lifecycle management.
-   **Performance:** `aiohttp` async transport, exponential backoff, TTL caching with LRU eviction, and per-key concurrency locking.
-   **Interfaces:** Modern FastAPI web server + feature-rich CLI.
-   **Reliable:** Comprehensive test suite with over 90% coverage.

## 🛠️ Installation

### Standard (Linux/macOS/Windows)
```bash
git clone https://github.com/your-repo/ff-api.git
cd ff-api
pip install -r requirements.txt
```

### Termux (Android)
```bash
pkg update && pkg upgrade
pkg install python binutils
pip install -r requirements.txt
```

## 🔑 Configuration (.env)

Copy `.env.example` to `.env` and fill in the required constants.

```env
# Garena guest credentials (from MajorLogin)
GARENA_GUEST_UID=12345...
GARENA_GUEST_TOKEN=abcde...

# AES Keys (from APK binary analysis)
AES_KEY=your_32_byte_hex_key
AES_IV=your_16_byte_hex_iv

# API Settings
OB_VERSION=OB53
SERVER_PORT=8080
```

### 🔍 Obtaining Credentials & Keys

1.  **JWT/Guest Token:** Capture traffic from a Free Fire guest login using HttpCanary or Burp Suite. Look for the `MajorLogin` request to `loginbp.ggblueshark.com`.
2.  **AES Constants:** These are typically found in the `libil2cpp.so` or `libunity.so` binaries. Community forums like *0xMe* or *hlgaming* often provide updated keys after every OB update.

## 🖥️ Usage

### Web Server (FastAPI)
```bash
python main.py --port 8080
```
-   **Player Info:** `GET /player?uid=4899748638&region=IND`
-   **Batch Info:** `GET /batch?uids=123,456&region=IND`
-   **Interactive Docs:** `http://localhost:8080/docs`

### CLI Interface
```bash
# Single fetch
python cli.py --uid 4899748638 --region IND

# Batch fetch from file
python cli.py --batch uids.txt --region IND

# JSON Compact format
python cli.py --uid 4899748638 --region IND --format compact
```

## 🧪 Testing

Run the full test suite to verify the pipeline:
```bash
python -m pytest
```

## 🛠️ Updates (New OB Release)

Garena typically updates the `OB_VERSION` and occasionally rotates AES keys every 2-3 months.
To update:
1. Edit `OB_VERSION` in your `.env`.
2. Update `AES_KEY` and `AES_IV` in `.env` if decryption errors occur.

## ⚖️ License
This project is for educational and research purposes only. Use responsibly.
