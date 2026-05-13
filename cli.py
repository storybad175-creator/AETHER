import argparse
import asyncio
import json
import sys
import logging
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from core.transport import transport

# ANSI Color Codes
CLR_G = "\033[92m" # Green
CLR_Y = "\033[93m" # Yellow
CLR_R = "\033[91m" # Red
CLR_C = "\033[96m" # Cyan
CLR_0 = "\033[0m"  # Reset

# Disable logging for CLI unless requested
logging.basicConfig(level=logging.ERROR)

async def run_batch(file_path: str, region: str, no_color: bool):
    """Processes a file containing UIDs concurrently (max 10)."""
    semaphore = asyncio.Semaphore(10)

    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

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

    except Exception as e:
        err_msg = f"{CLR_R}Batch Error: {e}{CLR_0}" if not no_color else f"Batch Error: {e}"
        print(err_msg, file=sys.stderr)
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
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colorized output")

    args = parser.parse_args()

    def color(text: str, code: str) -> str:
        return f"{code}{text}{CLR_0}" if not args.no_color else text

    if args.regions:
        print(color("Supported Regions:", CLR_C))
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(color("API Health Status:", CLR_C))
        print(json.dumps({"status": "ok", "interface": "CLI", "regions": len(REGION_MAP)}, indent=2))
        return

    if args.batch:
        if not args.region:
            print(color("Error: --region is required for batch mode", CLR_R), file=sys.stderr)
            sys.exit(1)
        await run_batch(args.batch, args.region, args.no_color)
        return

    if args.uid and args.region:
        try:
            result = await fetch_player(args.uid, args.region)
            indent = 2 if args.format == "pretty" else None
            output = result.model_dump_json(indent=indent)

            if args.format == "pretty" and not args.no_color:
                # Basic colorization for pretty JSON
                output = output.replace('"', color('"', CLR_Y))

            print(output)
        except Exception as e:
            print(color(f"Error: {e}", CLR_R), file=sys.stderr)
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
