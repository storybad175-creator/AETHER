# Free Fire UID Verification API — APEX v3.0

The definitive implementation for fetching Garena Free Fire player data using only UID and region.

## Features
- **All 14 Regions Supported**: IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA.
- **Protobuf Strategy**: Native Strategy B raw binary implementation for longevity.
- **AES-CBC Security**: Full payload encryption/decryption as used by Garena.
- **JWT Lifecycle**: Automatic guest token fetch and proactive refresh.
- **Async & Fast**: Built with FastAPI and aiohttp for high concurrency.
- **Resilient**: Exponential backoff, retry logic, and cache stampede protection.

## Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/ff-api.git
cd ff-api

# Install dependencies
pip install -r requirements.txt
```

## Setup

1. Copy `.env.example` to `.env`.
2. Fill in your `GARENA_GUEST_UID` and `GARENA_GUEST_TOKEN`.
3. Provide the latest `AES_KEY` and `AES_IV` extracted from the APK.

## Usage

### Running the Web Server
```bash
python main.py --port 8080
```

### Using the CLI
```bash
# Single UID
python cli.py --uid 4899748638 --region IND

# Batch Mode
python cli.py --batch uids.txt --region IND
```

## API Endpoints
- `GET /player?uid={uid}&region={region}`: Fetch player data.
- `GET /batch?uids={u1,u2}&region={region}`: Fetch multiple players.
- `GET /health`: Check server status.
- `GET /regions`: List all supported regions.

## Testing
```bash
pytest
```
