import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport
from config.settings import settings

# ANSI Color Codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

async def run_batch(file_path: str, region: str):
    """Processes a file containing UIDs and prints results as JSONL."""
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        # Process in batches of 10 for safety/performance
        for i in range(0, len(uids), 10):
            batch = uids[i:i+10]
            tasks = [fetch_player(uid, region) for uid in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for uid, res in zip(batch, results):
                if isinstance(res, Exception):
                    print(json.dumps({"uid": uid, "error": str(res)}), file=sys.stderr)
                else:
                    print(res.model_dump_json())
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
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    if args.regions:
        print(f"{Colors.HEADER}Supported Regions:{Colors.ENDC}")
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(f"{Colors.OKBLUE}Checking API Health...{Colors.ENDC}")
        print(json.dumps({
            "status": "ok",
            "ob_version": settings.OB_VERSION,
            "interface": "CLI"
        }, indent=2))
        return

    if args.batch:
        if not args.region:
            print(f"{Colors.FAIL}Error: --region is required for batch mode{Colors.ENDC}", file=sys.stderr)
            sys.exit(1)
        await run_batch(args.batch, args.region)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            output = result.model_dump_json(indent=indent)

            if sys.stdout.isatty() and args.format == "pretty":
                 # Simple colorization for JSON
                 print(f"{Colors.OKGREEN}{output}{Colors.ENDC}")
            else:
                 print(output)

        except Exception as e:
            print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}", file=sys.stderr)
            sys.exit(1)
        finally:
            await transport.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Aborted by user.{Colors.ENDC}")
        sys.exit(0)
