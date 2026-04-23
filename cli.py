import argparse
import asyncio
import json
import sys
import logging
import os
from typing import List
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport
from config.settings import settings

# Configure minimal logging for CLI
logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ff_cli")

async def run_batch(file_path: str, region: str, format_compact: bool):
    """
    Processes a file containing UIDs and prints results as JSON Lines (JSONL).
    Uses a concurrency limit of 10 to avoid Garena rate limits.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return

    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        if not uids:
            print(f"Warning: File {file_path} is empty.", file=sys.stderr)
            return

        # Concurrency limit implementation
        semaphore = asyncio.Semaphore(10)

        async def fetch_with_sem(uid: str):
            async with semaphore:
                try:
                    return await fetch_player(uid, region)
                except Exception as e:
                    return {"uid": uid, "error": str(e)}

        tasks = [fetch_with_sem(uid) for uid in uids]
        results = await asyncio.gather(*tasks)

        for res in results:
            if hasattr(res, "model_dump_json"):
                print(res.model_dump_json(indent=None if format_compact else 2))
            else:
                print(json.dumps(res))

    finally:
        await transport.close()

async def main_async():
    parser = argparse.ArgumentParser(
        description="Free Fire UID Verification CLI (APEX v3.0)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--uid", type=str, help="Single player UID to verify")
    parser.add_argument("--region", type=str, help="Region code (e.g., IND, BR, SG)")
    parser.add_argument("--batch", type=str, help="Path to text file containing UIDs (one per line)")
    parser.add_argument("--regions", action="store_true", help="List all supported region codes")
    parser.add_argument("--health", action="store_true", help="Perform health check on API config and JWT")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty", help="JSON output formatting")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.regions:
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(f"FF API OB Version: {settings.OB_VERSION}")
        print(f"Active Regions: {len(REGION_MAP)}")
        try:
            from core.auth import jwt_manager
            # This will trigger a refresh if credentials exist
            token = await jwt_manager.get_token()
            print(f"JWT Status: VALID (Token starts with: {token[:10]}...)")
        except Exception as e:
            print(f"JWT Status: FAILED ({str(e)})")
        return

    if args.batch:
        if not args.region:
            print("Error: --region is required for batch mode", file=sys.stderr)
            sys.exit(1)
        await run_batch(args.batch, args.region, args.format == "compact")
        return

    if args.uid:
        if not args.region:
            print("Error: --region is required for single lookup", file=sys.stderr)
            sys.exit(1)

        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            print(result.model_dump_json(indent=indent))
        except Exception as e:
            # Consistent error output in JSON format
            err_res = {
                "uid": args.uid,
                "region": args.region,
                "error": str(e),
                "type": type(e).__name__
            }
            print(json.dumps(err_res, indent=2), file=sys.stderr)
            sys.exit(1)
        finally:
            await transport.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(0)
