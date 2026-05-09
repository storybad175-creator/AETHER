import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport

# Disable logging for CLI unless requested
logging.basicConfig(level=logging.ERROR)

async def run_batch(file_path: str, region: str, use_color: bool = True):
    """Processes a file containing UIDs concurrently and prints results as JSONL."""
    semaphore = asyncio.Semaphore(10)

    async def fetch_with_sem(uid):
        async with semaphore:
            try:
                result = await fetch_player(uid, region)
                print(result.model_dump_json())
            except Exception as e:
                error_msg = f"Error fetching {uid}: {str(e)}"
                if use_color:
                    print(f"\033[91m{error_msg}\033[0m", file=sys.stderr)
                else:
                    print(error_msg, file=sys.stderr)

    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        await asyncio.gather(*(fetch_with_sem(uid) for uid in uids))
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
    use_color = not args.no_color

    if args.regions:
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        # Mock health check for CLI
        print(json.dumps({"status": "ok", "interface": "CLI"}, indent=2))
        return

    if args.batch:
        if not args.region:
            print("Error: --region is required for batch mode", file=sys.stderr)
            sys.exit(1)
        await run_batch(args.batch, args.region, use_color=use_color)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            print(result.model_dump_json(indent=indent))
        except Exception as e:
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
