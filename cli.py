import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport

# ANSI Color Codes
CLR_G = "\033[92m"
CLR_R = "\033[91m"
CLR_Y = "\033[93m"
CLR_B = "\033[94m"
CLR_0 = "\033[0m"

# Disable logging for CLI unless requested
logging.basicConfig(level=logging.ERROR)

async def safe_fetch_cli(uid: str, region: str, semaphore: asyncio.Semaphore):
    """Safely fetches player data with concurrency limit."""
    async with semaphore:
        try:
            return await fetch_player(uid, region)
        except Exception as e:
            return {"uid": uid, "error": str(e)}

async def run_batch(file_path: str, region: str):
    """Processes a file containing UIDs concurrently and prints results."""
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        semaphore = asyncio.Semaphore(10)
        tasks = [safe_fetch_cli(uid, region, semaphore) for uid in uids]

        results = await asyncio.gather(*tasks)
        for res in results:
            if isinstance(res, dict) and "error" in res:
                print(f"{CLR_R}Error {res['uid']}:{CLR_0} {res['error']}", file=sys.stderr)
            else:
                print(res.model_dump_json())
    except Exception as e:
        print(f"{CLR_R}Batch error:{CLR_0} {e}", file=sys.stderr)
    finally:
        await transport.close()

async def main():
    parser = argparse.ArgumentParser(description="Free Fire UID Verification CLI — APEX v3.0")
    parser.add_argument("--uid", type=str, help="Player UID to fetch")
    parser.add_argument("--region", type=str, help="Region code (e.g. IND, SG)")
    parser.add_argument("--batch", type=str, help="Path to file containing UIDs")
    parser.add_argument("--regions", action="store_true", help="List supported regions")
    parser.add_argument("--health", action="store_true", help="Check API health")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty", help="Output format")
    parser.add_argument("--no-color", action="store_true", help="Disable colorized output")

    args = parser.parse_args()

    # Handle no-color
    if args.no_color:
        global CLR_G, CLR_R, CLR_Y, CLR_B, CLR_0
        CLR_G = CLR_R = CLR_Y = CLR_B = CLR_0 = ""

    if args.regions:
        print(f"{CLR_B}Supported Regions:{CLR_0}")
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(f"{CLR_G}Status: OK{CLR_0} (Interface: CLI)")
        return

    if args.batch:
        if not args.region:
            print(f"{CLR_R}Error:{CLR_0} --region is required for batch mode", file=sys.stderr)
            sys.exit(1)
        await run_batch(args.batch, args.region)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            print(result.model_dump_json(indent=indent))
        except Exception as e:
            print(f"{CLR_R}Error:{CLR_0} {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            await transport.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{CLR_Y}Interrupted by user.{CLR_0}")
        sys.exit(0)
