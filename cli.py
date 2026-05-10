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

async def run_batch(file_path: str, region: str, format: str = "compact", semaphore_limit: int = 10):
    """Processes a file containing UIDs concurrently with a semaphore."""
    semaphore = asyncio.Semaphore(semaphore_limit)

    async def fetch_with_semaphore(uid: str):
        async with semaphore:
            try:
                result = await fetch_player(uid, region)
                return result
            except Exception as e:
                return {"uid": uid, "error": str(e)}

    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        tasks = [fetch_with_semaphore(uid) for uid in uids]
        results = await asyncio.gather(*tasks)

        for res in results:
            if isinstance(res, PlayerResponse):
                indent = 2 if format == "pretty" else None
                print(res.model_dump_json(indent=indent))
            else:
                print(json.dumps(res))
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
    parser.add_argument("--no-color", action="store_true", help="Disable colorized output")

    args = parser.parse_args()

    if args.regions:
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(json.dumps({
            "status": "ok",
            "interface": "CLI",
            "version": "3.0.0",
            "active_regions": len(REGION_MAP)
        }, indent=2))
        return

    if args.batch:
        if not args.region:
            print("Error: --region is required for batch mode", file=sys.stderr)
            sys.exit(1)
        await run_batch(args.batch, args.region, format=args.format)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            print(result.model_dump_json(indent=indent))
        except Exception as e:
            # Check for ANSI color support
            if not args.no_color and sys.stderr.isatty():
                print(f"\033[91mError: {e}\033[0m", file=sys.stderr)
            else:
                print(f"Error: {e}", file=sys.stderr)
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
