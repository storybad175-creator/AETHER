import asyncio
import argparse
import json
import sys
from typing import List
from core.fetcher import fetch_player
from api.schemas import PlayerResponse

async def run_cli():
    parser = argparse.ArgumentParser(description="Free Fire UID Verification CLI")
    parser.add_argument("--uid", type=str, help="Player UID")
    parser.add_argument("--region", type=str, help="Player Region (e.g. IND, BR, SG)")
    parser.add_argument("--batch", type=str, help="Path to text file with UIDs (one per line)")
    parser.add_argument("--format", type=str, choices=["pretty", "compact"], default="pretty", help="Output format")
    parser.add_argument("--regions", action="store_true", help="List all supported regions")
    parser.add_argument("--health", action="store_true", help="Check API health and OB version")

    args = parser.parse_args()

    if args.regions:
        from config.regions import REGION_MAP
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        from config.settings import settings
        print(json.dumps({"status": "ok", "ob_version": settings.OB_VERSION}, indent=2))
        return

    if args.batch:
        if not args.region:
            print("Error: --region is required when using --batch")
            sys.exit(1)

        try:
            with open(args.batch, 'r') as f:
                uids = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading batch file: {e}")
            sys.exit(1)

        # Process in chunks of 10 to respect gather limits
        results = []
        for i in range(0, len(uids), 10):
            chunk = uids[i:i+10]
            tasks = [fetch_player(uid, args.region) for uid in chunk]
            chunk_results = await asyncio.gather(*tasks)
            results.extend(chunk_results)

        for res in results:
            indent = 2 if args.format == "pretty" else None
            print(res.model_dump_json(by_alias=True, indent=indent))
        return

    if args.uid and args.region:
        result = await fetch_player(args.uid, args.region)
        indent = 2 if args.format == "pretty" else None
        print(result.model_dump_json(by_alias=True, indent=indent))
        if result.error:
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        pass
