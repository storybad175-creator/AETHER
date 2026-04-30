import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport
from api.schemas import PlayerResponse

# Disable logging for CLI unless requested
logging.basicConfig(level=logging.ERROR)

async def safe_fetch_cli(uid: str, region: str):
    """Fetches a player and handles exceptions for CLI reporting."""
    try:
        return await fetch_player(uid, region)
    except Exception as e:
        return {"uid": uid, "error": str(e)}

async def run_batch(file_path: str, region: str, format: str):
    """Processes a file containing UIDs concurrently with a limit of 10."""
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        # Process in chunks of 10
        concurrency_limit = 10
        for i in range(0, len(uids), concurrency_limit):
            chunk = uids[i:i + concurrency_limit]
            tasks = [safe_fetch_cli(uid, region) for uid in chunk]
            results = await asyncio.gather(*tasks)

            for result in results:
                if isinstance(result, PlayerResponse):
                    indent = 2 if format == "pretty" else None
                    print(result.model_dump_json(indent=indent))
                else:
                    print(json.dumps(result), file=sys.stderr)
    finally:
        await transport.close()

async def main():
    parser = argparse.ArgumentParser(description="Free Fire UID Verification CLI")
    parser.add_argument("--uid", type=str, help="Player UID to fetch")
    parser.add_argument("--region", type=str, help="Region code (e.g. IND, SG)")
    parser.add_argument("--batch", type=str, help="Path to file containing UIDs")
    parser.add_argument("--regions", action="store_true", help="List supported regions")
    parser.add_argument("--health", action="store_true", help="Check API health")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty", help="Output format")

    args = parser.parse_args()

    if args.regions:
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(json.dumps({"status": "ok", "interface": "CLI"}, indent=2))
        return

    if args.batch:
        if not args.region:
            print("Error: --region is required for batch mode", file=sys.stderr)
            sys.exit(1)
        await run_batch(args.batch, args.region, args.format)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            print(result.model_dump_json(indent=indent))
        except Exception as e:
            print(json.dumps({"uid": args.uid, "error": str(e)}), file=sys.stderr)
            sys.exit(1)
        finally:
            await transport.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
