import argparse
import asyncio
import json
import sys
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from config.settings import settings
from api.errors import FFError

def print_banner():
    banner = """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║        FREE FIRE UID VERIFICATION API — APEX v3.0 UNLIMITED         ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def run_fetch(uid: str, region: str, compact: bool):
    try:
        result = await fetch_player(uid, region)
        indent = None if compact else 2
        print(json.dumps(result, indent=indent, ensure_ascii=False))
    except FFError as e:
        error_res = {
            "metadata": {
                "request_uid": uid,
                "request_region": region,
                "fetched_at": "",
                "response_time_ms": 0,
                "api_version": settings.OB_VERSION,
                "cache_hit": False
            },
            "data": None,
            "error": {
                "code": e.code,
                "message": e.message,
                "retryable": e.retryable,
                "extra": e.extra
            }
        }
        print(json.dumps(error_res, indent=2), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

async def run_batch(file_path: str, region: str):
    try:
        with open(file_path, 'r') as f:
            uids = [line.strip() for line in f if line.strip()]

        tasks = [fetch_player(uid, region) for uid in uids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, Exception):
                print(json.dumps({"error": str(res)}))
            else:
                print(json.dumps(res))
    except Exception as e:
        print(f"Error reading batch file: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Free Fire UID Verification CLI")
    parser.add_argument("--uid", type=str, help="Player UID")
    parser.add_argument("--region", type=str, help="Player region")
    parser.add_argument("--batch", type=str, help="Path to file containing UIDs (one per line)")
    parser.add_argument("--format", type=str, choices=["pretty", "compact"], default="pretty", help="Output format")
    parser.add_argument("--regions", action="store_true", help="List supported regions")
    parser.add_argument("--health", action="store_true", help="Check system health")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI server")
    parser.add_argument("--port", type=int, default=settings.SERVER_PORT, help="Port for the FastAPI server")

    args = parser.parse_args()

    if args.serve:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=args.port)
        return

    if args.regions:
        print(json.dumps(list(REGION_MAP.keys()), indent=2))
        return

    if args.health:
        print(json.dumps({
            "status": "ok",
            "ob_version": settings.OB_VERSION,
            "regions": len(REGION_MAP)
        }, indent=2))
        return

    if args.batch:
        if not args.region:
            print("Error: --region is required for batch processing", file=sys.stderr)
            sys.exit(1)
        asyncio.run(run_batch(args.batch, args.region))
        return

    if args.uid and args.region:
        print_banner()
        asyncio.run(run_fetch(args.uid, args.region, args.format == "compact"))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
