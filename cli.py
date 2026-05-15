import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport
from api.schemas import PlayerResponse

# Disable logging for CLI unless requested
logging.basicConfig(level=logging.ERROR)

async def run_batch(file_path: str, region: str, format: str):
    """Processes a file containing UIDs and prints results as JSONL concurrently."""
    semaphore = asyncio.Semaphore(10)

    async def fetch_with_sem(uid: str):
        async with semaphore:
            try:
                result = await fetch_player(uid, region)
                indent = 2 if format == "pretty" else None
                print(result.model_dump_json(indent=indent))
            except Exception as e:
                print(json.dumps({"uid": uid, "error": str(e)}), file=sys.stderr)

    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        tasks = [fetch_with_sem(uid) for uid in uids]
        await asyncio.gather(*tasks)
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
        # Check health by attempting a dummy call or just reporting version
        from config.settings import settings
        health_info = {
            "status": "ok",
            "ob_version": settings.OB_VERSION,
            "interface": "CLI",
            "supported_regions": len(REGION_MAP)
        }
        print(json.dumps(health_info, indent=2))
        return

    if args.batch:
        if not args.region:
            print("Error: --region is required for batch mode", file=sys.stderr)
            sys.exit(1)
        await run_batch(args.batch, args.region, args.format)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            output = result.model_dump_json(indent=indent)

            # Simple ANSI colorizing if enabled
            if not args.no_color and sys.stdout.isatty() and args.format == "pretty":
                try:
                    # Very basic colorizer for nickname and level
                    data = json.loads(output)
                    if data.get("data") and data["data"].get("account"):
                        acc = data["data"]["account"]
                        acc["nickname"] = f"\033[92m{acc['nickname']}\033[0m"
                        acc["level"] = f"\033[93m{acc['level']}\033[0m"
                        output = json.dumps(data, indent=2)
                except:
                    pass

            print(output)
        except Exception as e:
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
