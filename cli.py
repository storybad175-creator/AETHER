import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport
from api.schemas import PlayerResponse

# ANSI Color Codes
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Disable logging for CLI unless requested
logging.basicConfig(level=logging.ERROR)

async def run_batch(file_path: str, region: str, concurrency: int = 10):
    """Processes a file containing UIDs concurrently and prints results as JSONL."""
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        semaphore = asyncio.Semaphore(concurrency)

        async def sem_fetch(uid):
            async with semaphore:
                try:
                    result = await fetch_player(uid, region)
                    return result
                except Exception as e:
                    return {"uid": uid, "error": str(e)}

        tasks = [sem_fetch(uid) for uid in uids]
        results = await asyncio.gather(*tasks)

        for res in results:
            if isinstance(res, PlayerResponse):
                print(res.model_dump_json())
            else:
                print(json.dumps(res), file=sys.stderr)
    finally:
        await transport.close()

async def main():
    parser = argparse.ArgumentParser(description="Free Fire UID Verification CLI — APEX v3.0 UNLIMITED")
    parser.add_argument("--uid", type=str, help="Player UID to fetch")
    parser.add_argument("--region", type=str, help="Region code (e.g. IND, SG)")
    parser.add_argument("--batch", type=str, help="Path to file containing UIDs")
    parser.add_argument("--regions", action="store_true", help="List supported regions")
    parser.add_argument("--health", action="store_true", help="Check API health")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty", help="Output format")
    parser.add_argument("--no-color", action="store_true", help="Disable colorized output")

    args = parser.parse_args()

    def colorize(text, color):
        if args.no_color or not sys.stdout.isatty():
            return text
        return f"{color}{text}{RESET}"

    if args.regions:
        print(colorize("Supported Regions:", CYAN))
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(colorize("API Status: OK", GREEN))
        print(json.dumps({"status": "ok", "interface": "CLI", "version": "v3.0"}, indent=2))
        return

    if args.batch:
        if not args.region:
            print(colorize("Error: --region is required for batch mode", RED), file=sys.stderr)
            sys.exit(1)
        await run_batch(args.batch, args.region)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None

            output = result.model_dump_json(indent=indent)
            if not args.no_color:
                print(colorize("Fetch Successful!", GREEN))

            print(output)
        except Exception as e:
            print(colorize(f"Error: {e}", RED), file=sys.stderr)
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
