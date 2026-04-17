# FREE FIRE UID VERIFICATION API — APEX v3.0

A production-ready, multi-region Python API for fetching Free Fire player data using only their UID and Region.

## Features

- **Multi-Region Support**: All 14 Garena regions (IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA).
- **Dual Protobuf Strategy**: Uses compiled `.proto` classes for performance, with a raw binary fallback.
- **AES-CBC Encryption**: Correct implementation of Garena's wire protocol encryption.
- **JWT Lifecycle**: Automatic guest account authentication and token refreshing.
- **Advanced Caching**: TTL-based in-memory cache with LRU eviction and concurrency locks.
- **High Performance**: Built with `FastAPI` and `aiohttp` for asynchronous efficiency.
- **Validation**: Strict Pydantic v2 schemas for all inputs and outputs.
- **CLI & Web**: Full argparse CLI and production FastAPI server included.

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/ff-api.git
   cd ff-api
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Garena guest credentials and AES keys
   ```

### Termux (Android)
```bash
pkg install python ndk-sysroot clang make
pip install -r requirements.txt
```

## Usage

### Starting the Server
```bash
python main.py
```
Server runs on `http://localhost:8080` by default.

### Using the CLI
```bash
# Fetch a single player
python cli.py --uid 4899748638 --region IND

# Batch processing from file
python cli.py --batch uids.txt --region SG --format compact

# List regions
python cli.py --regions
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/player` | GET | Fetch data for a single UID & Region |
| `/batch` | GET | Fetch data for up to 10 UIDs concurrently |
| `/health` | GET | Check system status and OB version |
| `/regions` | GET | List all supported region codes |

## Development

### Running Tests
```bash
pytest
```

### Updating OB Version
When a new Free Fire update drops (e.g., OB54), simply update the `OB_VERSION` in your `.env` file. No code changes required.

## Credits & Methodology
AES keys and Protobuf mappings are community-extracted from Free Fire APK analysis. This tool is for educational purposes and should be used responsibly according to Garena's TOS.
