import asyncio
import argparse
import json
import sys
from core.fetcher import fetch_player
from config.regions import REGION_MAP

async def run_cli():
    parser = argparse.ArgumentParser(description="Free Fire UID Verification CLI")
    parser.add_argument("--uid", type=str, help="Player UID")
    parser.add_argument("--region", type=str, help="Player Region")
    parser.add_argument("--batch", type=str, help="Path to file containing UIDs (one per line)")
    parser.add_argument("--regions", action="store_true", help="List all supported regions")
    parser.add_argument("--format", type=str, choices=["pretty", "compact"], default="pretty", help="Output format")

    args = parser.parse_args()

    if args.regions:
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.batch:
        try:
            with open(args.batch, "r") as f:
                uids = [line.strip() for line in f if line.strip()]
            tasks = [fetch_player(uid, args.region) for uid in uids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                print(json.dumps(res.model_dump() if not isinstance(res, Exception) else {"error": str(res)},
                                 indent=None if args.format == "compact" else 2))
        except Exception as e:
            print(f"Error reading batch file: {e}", file=sys.stderr)
            sys.exit(1)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            print(json.dumps(result.model_dump(), indent=None if args.format == "compact" else 2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(run_cli())
