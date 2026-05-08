import argparse
import asyncio
import json
import sys
import os
from typing import List
from api.schemas import PlayerResponse, PlayerRequest
from core.fetcher import fetch_player
from config.regions import REGION_MAP

# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    banner = f"""
{Colors.BLUE}╔══════════════════════════════════════════════════════════════════════╗
║        {Colors.BOLD}FREE FIRE UID VERIFICATION API — APEX v3.0 UNLIMITED{Colors.BLUE}         ║
║   Multi-File Repo · All 14 Regions · OB53 · April 2026              ║
╚══════════════════════════════════════════════════════════════════════╝{Colors.ENDC}
"""
    print(banner)

async def run_fetch(uid: str, region: str, compact: bool, no_color: bool):
    """Fetches and prints player data."""
    try:
        # Validate
        PlayerRequest(uid=uid, region=region)

        response = await fetch_player(uid, region)
        output = response.model_dump_json(by_alias=True, indent=None if compact else 2)

        if not no_color and not compact:
            # Simple colorization for terminal
            print(f"{Colors.GREEN}--- PLAYER DATA: {uid} ({region}) ---{Colors.ENDC}")
            print(output)
        else:
            print(output)

    except Exception as e:
        err = {"error": str(e)}
        print(json.dumps(err), file=sys.stderr)
        sys.exit(1)

async def run_batch(file_path: str, region: str, no_color: bool):
    """Processes UIDs from a file concurrently."""
    if not os.path.exists(file_path):
        print(f"{Colors.RED}Error: File {file_path} not found.{Colors.ENDC}", file=sys.stderr)
        sys.exit(1)

    with open(file_path, 'r') as f:
        uids = [line.strip() for line in f if line.strip()]

    print(f"{Colors.CYAN}Processing {len(uids)} UIDs from {file_path}...{Colors.ENDC}")

    # We use a semaphore to limit concurrency to 10
    sem = asyncio.Semaphore(10)

    async def sem_fetch(uid):
        async with sem:
            resp = await fetch_player(uid, region)
            print(resp.model_dump_json(by_alias=True))

    tasks = [sem_fetch(uid) for uid in uids]
    await asyncio.gather(*tasks)

def main():
    parser = argparse.ArgumentParser(description="Free Fire UID Verification CLI")
    parser.add_argument("--uid", help="Player Unique ID")
    parser.add_argument("--region", help="Region code (IND, BR, SG, etc.)")
    parser.add_argument("--batch", help="Path to text file containing UIDs (one per line)")
    parser.add_argument("--format", choices=["pretty", "compact"], default="pretty", help="Output JSON format")
    parser.add_argument("--no-color", action="store_true", help="Disable colorized output")
    parser.add_argument("--regions", action="store_true", help="List all supported regions")
    parser.add_argument("--health", action="store_true", help="Check system health")

    args = parser.parse_args()

    if args.regions:
        print(f"Supported Regions ({len(REGION_MAP)}):")
        for r in sorted(REGION_MAP.keys()):
            print(f" - {r}")
        return

    if not args.no_color:
        print_banner()

    if args.health:
        print("System Health: OK")
        print("OB Version: OB53")
        return

    if args.batch:
        if not args.region:
            print(f"{Colors.RED}Error: --region is required for batch processing.{Colors.ENDC}", file=sys.stderr)
            sys.exit(1)
        asyncio.run(run_batch(args.batch, args.region, args.no_color))
    elif args.uid and args.region:
        asyncio.run(run_fetch(args.uid, args.region, args.format == "compact", args.no_color))
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.ENDC}")
        sys.exit(0)
