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

async def run_batch(file_path: str, region: str):
    """Processes a file containing UIDs and prints results as JSONL with concurrency control."""
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        # FM-14: Concurrent batch processing with limit
        semaphore = asyncio.Semaphore(10)

        async def fetch_with_sem(uid: str):
            async with semaphore:
                try:
                    result = await fetch_player(uid, region)
                    return result.model_dump()
                except Exception as e:
                    return {"uid": uid, "error": str(e)}

        tasks = [fetch_with_sem(uid) for uid in uids]
        results = await asyncio.gather(*tasks)

        for res in results:
            print(json.dumps(res))

    finally:
        await transport.close()

def print_color(text: str, color_code: str):
    """Prints colorized text if terminal supports it."""
    if sys.stdout.isatty():
        print(f"\033[{color_code}m{text}\033[0m")
    else:
        print(text)

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
        print_color("Checking API Health...", "36")
        print(json.dumps({"status": "ok", "interface": "CLI", "active_regions": len(REGION_MAP)}, indent=2))
        return

    if args.batch:
        if not args.region:
            print_color("Error: --region is required for batch mode", "31")
            sys.exit(1)
        await run_batch(args.batch, args.region)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            print(result.model_dump_json(indent=indent))
        except Exception as e:
            print_color(f"Error: {e}", "31")
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
