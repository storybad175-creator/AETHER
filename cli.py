import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport
from api.errors import FFError

# Disable logging for CLI unless requested
logging.basicConfig(level=logging.ERROR)

async def safe_fetch_cli(uid: str, region: str):
    """Wraps fetch_player for CLI usage with error handling."""
    try:
        result = await fetch_player(uid, region)
        return result.model_dump()
    except FFError as e:
        return {
            "uid": uid,
            "error": {
                "code": e.code,
                "message": e.message,
                "extra": e.extra
            }
        }
    except Exception as e:
        return {
            "uid": uid,
            "error": {
                "code": "UNKNOWN_ERROR",
                "message": str(e)
            }
        }

async def run_batch(file_path: str, region: str):
    """Processes a file containing UIDs and prints results as JSONL."""
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        # Concurrency limit of 10 for batch processing
        semaphore = asyncio.Semaphore(10)

        async def limited_fetch(uid):
            async with semaphore:
                return await safe_fetch_cli(uid, region)

        tasks = [limited_fetch(uid) for uid in uids]
        results = await asyncio.gather(*tasks)

        for res in results:
            print(json.dumps(res))

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
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
        await run_batch(args.batch, args.region)
        return

    if args.uid and args.region:
        try:
            result = await safe_fetch_cli(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            print(json.dumps(result, indent=indent))
        finally:
            await transport.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
