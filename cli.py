import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport

# ANSI Color codes
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Disable logging for CLI unless requested
logging.basicConfig(level=logging.ERROR)

async def run_batch(file_path: str, region: str, format: str, no_color: bool):
    """Processes a file containing UIDs concurrently and prints results as JSONL."""
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        semaphore = asyncio.Semaphore(10)

        async def fetch_with_sem(uid: str):
            async with semaphore:
                try:
                    result = await fetch_player(uid, region)
                    indent = 2 if format == "pretty" else None
                    output = result.model_dump_json(indent=indent)
                    if not no_color and format == "pretty":
                        print(f"{GREEN}{output}{RESET}")
                    else:
                        print(output)
                except Exception as e:
                    err_json = json.dumps({"uid": uid, "error": str(e)})
                    if not no_color:
                        print(f"{RED}{err_json}{RESET}", file=sys.stderr)
                    else:
                        print(err_json, file=sys.stderr)

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

    if args.regions:
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(json.dumps({"status": "ok", "interface": "CLI"}, indent=2))
        return

    if args.batch:
        if not args.region:
            print(f"{RED}Error: --region is required for batch mode{RESET}" if not args.no_color else "Error: --region is required for batch mode", file=sys.stderr)
            sys.exit(1)
        await run_batch(args.batch, args.region, args.format, args.no_color)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            output = result.model_dump_json(indent=indent)
            if not args.no_color and args.format == "pretty":
                print(f"{CYAN}{output}{RESET}")
            else:
                print(output)
        except Exception as e:
            if not args.no_color:
                print(f"{RED}Error: {e}{RESET}", file=sys.stderr)
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
