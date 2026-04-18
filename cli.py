import argparse
import asyncio
import json
import sys
import os
from core.fetcher import fetch_player
from core.transport import transport
from config.regions import REGION_MAP

async def run_fetch(uid: str, region: str, compact: bool):
    try:
        response = await fetch_player(uid, region)
        indent = None if compact else 2
        print(json.dumps(response.model_dump(), indent=indent, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    finally:
        await transport.close()

async def run_batch(file_path: str, region: str, compact: bool):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(file_path, "r") as f:
        uids = [line.strip() for line in f if line.strip()]

    tasks = [fetch_player(uid, region) for uid in uids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    indent = None if compact else 2
    for res in results:
        if isinstance(res, Exception):
            print(json.dumps({"error": str(res)}), file=sys.stderr)
        else:
            print(json.dumps(res.model_dump(), indent=indent, ensure_ascii=False))

    await transport.close()

def main():
    parser = argparse.ArgumentParser(description="Free Fire API CLI")
    parser.add_argument("--uid", type=str, help="Player UID")
    parser.add_argument("--region", type=str, help="Region code (e.g. IND, BR)")
    parser.add_argument("--batch", type=str, help="Path to file containing UIDs (one per line)")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty", help="Output format")
    parser.add_argument("--regions", action="store_true", help="List supported regions")
    parser.add_argument("--health", action="store_true", help="Check API health")

    args = parser.parse_args()
    compact = args.format == "compact"

    if args.regions:
        print("Supported Regions:", ", ".join(REGION_MAP.keys()))
        return

    if args.health:
        # Simple health check
        print(json.dumps({"status": "ok", "cli_version": "3.0.0"}))
        return

    if not args.region:
        print("Error: --region is required.")
        parser.print_help()
        sys.exit(1)

    if args.uid:
        asyncio.run(run_fetch(args.uid, args.region, compact))
    elif args.batch:
        asyncio.run(run_batch(args.batch, args.region, compact))
    else:
        print("Error: Either --uid or --batch is required.")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
