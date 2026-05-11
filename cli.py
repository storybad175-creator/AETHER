import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport

# ANSI Color support
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def colorize(text, color, no_color=False):
    if no_color:
        return text
    return f"{color}{text}{Colors.ENDC}"

async def run_batch(file_path: str, region: str, semaphore: asyncio.Semaphore):
    """Processes a file containing UIDs and prints results as JSONL."""
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        async def fetch_with_sem(uid):
            async with semaphore:
                try:
                    result = await fetch_player(uid, region)
                    return result.model_dump_json()
                except Exception as e:
                    return json.dumps({"uid": uid, "error": str(e)})

        tasks = [fetch_with_sem(uid) for uid in uids]
        results = await asyncio.gather(*tasks)
        for res in results:
            print(res)
    except Exception as e:
        print(colorize(f"Batch Error: {e}", Colors.FAIL), file=sys.stderr)
    finally:
        await transport.close()

async def main():
    parser = argparse.ArgumentParser(description="Free Fire UID Verification CLI — APEX v3.0")
    parser.add_argument("--uid", type=str, help="Player UID to fetch")
    parser.add_argument("--region", type=str, help="Region code (e.g. IND, SG)")
    parser.add_argument("--batch", type=str, help="Path to file containing UIDs")
    parser.add_argument("--regions", action="store_true", help="List supported regions")
    parser.add_argument("--health", action="store_true", help="Check local status")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty", help="Output format")
    parser.add_argument("--no-color", action="store_true", help="Disable colorized output")

    args = parser.parse_args()

    if args.regions:
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(colorize("--- Health Check ---", Colors.HEADER, args.no_color))
        print(f"Status: {colorize('OK', Colors.OKGREEN, args.no_color)}")
        print(f"Interface: {colorize('CLI', Colors.OKBLUE, args.no_color)}")
        return

    if args.batch:
        if not args.region:
            print(colorize("Error: --region is required for batch mode", Colors.FAIL, args.no_color), file=sys.stderr)
            sys.exit(1)
        sem = asyncio.Semaphore(10) # Max 10 concurrent requests
        await run_batch(args.batch, args.region, sem)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            output = result.model_dump_json(indent=indent)

            if args.format == "pretty" and not args.no_color:
                print(colorize("--- Player Data Retrieved ---", Colors.OKGREEN))

            print(output)
        except Exception as e:
            print(colorize(f"Error: {e}", Colors.FAIL, args.no_color), file=sys.stderr)
            sys.exit(1)
        finally:
            await transport.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
