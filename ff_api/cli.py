import argparse
import asyncio
import json
import sys
from ff_api.core.fetcher import fetch_player
from ff_api.config.regions import REGION_MAP
from ff_api.api.errors import FFError

async def run_cli():
    parser = argparse.ArgumentParser(description="Free Fire API CLI")
    parser.add_argument("--uid", type=str, help="Player UID")
    parser.add_argument("--region", type=str, help="Player Region")
    parser.add_argument("--batch", type=str, help="Path to file with UIDs")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty")
    parser.add_argument("--regions", action="store_true", help="List supported regions")
    parser.add_argument("--health", action="store_true", help="Check system health")

    args = parser.parse_args()

    if args.regions:
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        # Simple health check
        print(json.dumps({"status": "ok", "timestamp": asyncio.get_event_loop().time()}, indent=2))
        return

    if args.batch:
        if not args.region:
            print("Error: --region is required for batch mode.")
            sys.exit(1)
        try:
            with open(args.batch, "r") as f:
                uids = [line.strip() for line in f if line.strip()]

            tasks = [fetch_player(uid, args.region) for uid in uids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, FFError):
                    print(json.dumps({"error": res.message}, indent=None if args.format == "compact" else 2))
                elif isinstance(res, Exception):
                    print(json.dumps({"error": str(res)}, indent=None if args.format == "compact" else 2))
                else:
                    print(res.model_dump_json(indent=None if args.format == "compact" else 2, by_alias=True))
        except FileNotFoundError:
            print(f"Error: File {args.batch} not found.")
            sys.exit(1)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            print(result.model_dump_json(indent=None if args.format == "compact" else 2, by_alias=True))
        except FFError as e:
            print(json.dumps({"error": e.message, "code": e.code}, indent=2), file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        pass
