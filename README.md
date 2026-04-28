# Free Fire UID Verification API — APEX v3.0 UNLIMITED

The gold standard multi-region player data fetching API for Free Fire. Supporting all 14 official Garena regions with full Protobuf serialization and AES-CBC encryption.

## 🚀 Features

- **All 14 Regions Supported:** IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA.
- **OB53 Ready:** Optimized for the April 2026 update.
- **Full Data Coverage:** Account info, ranks, stats, guild, pet, cosmetics, and ban status.
- **Advanced Core:** Recursive Protobuf Strategy B parser + AES-CBC crypto.
- **Production Ready:** JWT auto-refresh, exponential backoff, TTL LRU cache, and rate limiting.
- **Dual Interface:** FastAPI Web Server + argparse CLI.
- **Low RAM Optimized:** Runs on Termux, shared hosting, and 1GB RAM devices.

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/ff-uid-api.git
cd ff-uid-api

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your credentials (see below)
```

## 🔑 Configuration

Edit the `.env` file with the following mandatory values:

### Garena Guest Credentials
Garena uses JWT tokens for authentication. You can extract guest credentials from a real Free Fire client using tools like Frida or by sniffing HTTPS traffic to `https://loginbp.ggblueshark.com/MajorLogin`.

- `GARENA_GUEST_UID`: Your extracted guest account UID.
- `GARENA_GUEST_TOKEN`: Your extracted guest account token.

### AES Constants
These are rotated by Garena occasionally (usually every major OB update).
- `AES_KEY`: 32-byte hex string.
- `AES_IV`: 16-byte hex string.

## 🖥️ Usage

### Web Server (FastAPI)
```bash
# Start the server
python main.py --port 8080
```
- **Endpoints:**
  - `GET /player?uid={UID}&region={REG}`: Fetch single player.
  - `GET /batch?uids={U1,U2}&region={REG}`: Fetch up to 10 players.
  - `GET /health`: System status.
  - `GET /regions`: List all 14 regions.

### CLI
```bash
# Single UID
python cli.py --uid 1234567890 --region IND

# Batch from file
python cli.py --batch uids.txt --region SG

# List regions
python cli.py --regions
```

## 🧪 Testing

```bash
# Run the test suite
pytest
```

## 📜 License
Definitive implementation for community educational purposes. Use responsibly.
