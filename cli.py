import asyncio
import argparse
import json
import sys
from typing import List
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from api.errors import FFError

async def run_fetch(uid: str, region: str, compact: bool):
    try:
        response = await fetch_player(uid, region)
        indent = None if compact else 2
        print(json.dumps(response.model_dump(), indent=indent))
    except FFError as e:
        error_res = {
            "metadata": {
                "request_uid": uid,
                "request_region": region,
                "api_version": "OB53",
                "cache_hit": False
            },
            "data": None,
            "error": {
                "code": e.code,
                "message": e.message,
                "retryable": e.retryable
            }
        }
        print(json.dumps(error_res, indent=2), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

async def run_batch(file_path: str, region: str):
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        tasks = [fetch_player(uid, region) for uid in uids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, Exception):
                print(json.dumps({"error": str(res)}))
            else:
                print(json.dumps(res.model_dump()))
    except Exception as e:
        print(f"Batch Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(prog="ff", description="Free Fire Player Data CLI")
    parser.add_argument("--uid", type=str, help="Player UID")
    parser.add_argument("--region", type=str, help="Region code")
    parser.add_argument("--batch", type=str, help="Path to text file containing UIDs")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty", help="Output format")
    parser.add_argument("--regions", action="store_true", help="List all supported regions")
    parser.add_argument("--health", action="store_true", help="Check API health")

    args = parser.parse_args()

    if args.regions:
        print("Supported Regions:", ", ".join(REGION_MAP.keys()))
        return

    if args.health:
        print("FF API Status: OK")
        print("Version: OB53")
        return

    if args.batch:
        if not args.region:
            print("Error: --region is required for batch mode", file=sys.stderr)
            sys.exit(1)
        asyncio.run(run_batch(args.batch, args.region))
    elif args.uid and args.region:
        asyncio.run(run_fetch(args.uid, args.region, args.format == "compact"))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
