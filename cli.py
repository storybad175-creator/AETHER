import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport
from api.errors import FFError

# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

async def run_batch(file_path: str, region: str, concurrency: int = 10):
    """Processes a file containing UIDs concurrently with a semaphore."""
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        semaphore = asyncio.Semaphore(concurrency)

        async def sem_fetch(uid):
            async with semaphore:
                try:
                    return await fetch_player(uid, region)
                except Exception as e:
                    return {"uid": uid, "error": str(e)}

        tasks = [sem_fetch(uid) for uid in uids]
        results = await asyncio.gather(*tasks)

        for res in results:
            if isinstance(res, dict):
                print(json.dumps(res))
            else:
                print(res.model_dump_json())

    except Exception as e:
        print(f"{Colors.FAIL}Batch error: {e}{Colors.ENDC}", file=sys.stderr)
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

    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith("__"):
                setattr(Colors, attr, "")

    if args.regions:
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(f"{Colors.OKGREEN}{json.dumps({'status': 'ok', 'interface': 'CLI', 'regions': 14}, indent=2)}{Colors.ENDC}")
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
            print(result.model_dump_json(indent=indent))
        except FFError as e:
            print(f"{Colors.FAIL}API Error [{e.code}]: {e.message}{Colors.ENDC}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"{Colors.FAIL}Unexpected Error: {e}{Colors.ENDC}", file=sys.stderr)
            sys.exit(1)
        finally:
            await transport.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    # Disable default logging to keep CLI output clean
    logging.getLogger().setLevel(logging.ERROR)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
