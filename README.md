# Free Fire UID Verification API — APEX v3.0

Production-ready API for fetching Free Fire player data across all 14 regions.

## Features
- All 14 Garena regions supported.
- Protocol Buffer binary serialization.
- AES-CBC payload encryption.
- JWT authentication lifecycle management.
- TTL Cache with LRU eviction.
- FastAPI web server & Argparse CLI.

## Setup
1. `pip install -r requirements.txt`
2. `cp .env.example .env`
3. Edit `.env` with your Garena Guest UID and Token.

## Usage
### Web Server
`python main.py`

### CLI
`python cli.py --uid 12345678 --region IND`

## Endpoints
- `GET /player?uid={uid}&region={region}`
- `GET /batch?uids={u1,u2}&region={region}`
- `GET /regions`
- `GET /health`
