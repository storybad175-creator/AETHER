# Free Fire UID Verification API — APEX v3.0

A production-ready, high-performance asynchronous Python API for extracting comprehensive player data from Garena's Free Fire servers across all 14 regions.

## Features

- **Multi-Region Support**: All 14 regions (IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA).
- **Asynchronous Architecture**: Built on FastAPI and aiohttp for high concurrency.
- **Robust Pipeline**: Reverse-engineered wire protocol with AES-CBC encryption and Protobuf serialization.
- **JWT Management**: Automatic lifecycle handling for Garena MajorLogin guest tokens.
- **Advanced Caching**: In-memory TTL cache with LRU eviction and concurrency locks.
- **Comprehensive Data**: Fetches 60+ fields including account info, ranks, detailed stats, guild, pets, and ban status.
- **CLI & Web**: Includes both a full FastAPI web server and a feature-rich CLI tool.

## Installation

### Standard Setup
```bash
git clone <repo-url>
cd ff_api
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### Termux (Android)
```bash
pkg install python
pip install -r requirements.txt
```

## Configuration

Edit the `.env` file with the following required values:

1. **GARENA_GUEST_UID / TOKEN**: Obtain these by intercepting the `MajorLogin` request from the Free Fire client using tools like HttpCanary or PCAPRemote.
2. **AES_KEY / IV**: Community-extracted 32-byte (key) and 16-byte (IV) hex strings.

## Usage

### Starting the API Server
```bash
python main.py --port 8080
```

### Using the CLI
```bash
# Fetch a single player
python cli.py --uid 123456789 --region IND

# Batch fetch from file
python cli.py --batch uids.txt --region SG

# List regions
python cli.py --regions
```

## API Endpoints

- `GET /api/v1/player?uid={uid}&region={region}`: Fetch detailed player profile.
- `GET /api/v1/batch?uids={u1,u2}&region={region}`: Concurrent fetch for multiple UIDs.
- `GET /api/v1/regions`: List supported region codes.
- `GET /api/v1/health`: System status and OB version info.

## Data Schema

The API returns a structured JSON response containing:
- **Account**: Level, EXP, Nickname, Creation/Last Login dates, Signature, etc.
- **Rank**: BR and CS rank names, codes, and points.
- **Stats**: Detailed BR (Solo/Duo/Squad) and CS Ranked statistics.
- **Social**: Guild information including leader details.
- **Pet**: Active pet name, level, and skill.
- **Cosmetics**: Equipped avatar, banner, outfits, and weapon skins.
- **Ban**: Real-time ban status and period.

## Maintenance

To update for a new game version (e.g., OB54):
1. Update `OB_VERSION` in `.env`.
2. If encryption keys changed, update `AES_KEY` and `AES_IV` in `.env`.

---
*Disclaimer: This project is for educational and research purposes only. All data is fetched from public endpoints.*
