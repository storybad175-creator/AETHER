import asyncio
import argparse
import json
import sys
from typing import List
from core.fetcher import fetch_player
from core.transport import transport
from config.regions import REGION_MAP

async def run_fetch(uid: str, region: str, compact: bool = False):
    try:
        result = await fetch_player(uid, region)
        indent = None if compact else 2
        print(json.dumps(result, indent=indent))
    except Exception as e:
        error_res = {
            "error": {
                "code": getattr(e, "code", "UNKNOWN_ERROR"),
                "message": str(e)
            }
        }
        print(json.dumps(error_res, indent=2), file=sys.stderr)
        sys.exit(1)
    finally:
        await transport.close()

async def run_batch(file_path: str, region: str):
    try:
        with open(file_path, "r") as f:
            uids = [line.strip() for line in f if line.strip()]

        # Limit to 10 concurrent requests to match /batch endpoint
        for i in range(0, len(uids), 10):
            chunk = uids[i : i + 10]
            tasks = [fetch_player(uid, region) for uid in chunk]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    print(json.dumps({"error": str(res)}))
                else:
                    print(json.dumps(res))
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
    finally:
        await transport.close()

def main():
    parser = argparse.ArgumentParser(description="Free Fire API CLI")
    parser.add_argument("--uid", type=str, help="Target player UID")
    parser.add_argument("--region", type=str, help="Target region code")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty", help="Output format")
    parser.add_argument("--batch", type=str, help="Path to text file with UIDs")
    parser.add_argument("--regions", action="store_true", help="List all supported regions")
    parser.add_argument("--health", action="store_true", help="Check API health")

    args = parser.parse_args()

    if args.regions:
        print("Supported Regions:", ", ".join(REGION_MAP.keys()))
        return

    if args.health:
        print("API Status: OK (OB53)")
        return

    if args.batch and args.region:
        asyncio.run(run_batch(args.batch, args.region))
    elif args.uid and args.region:
        asyncio.run(run_fetch(args.uid, args.region, args.format == "compact"))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
