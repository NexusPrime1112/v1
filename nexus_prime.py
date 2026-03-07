#!/usr/bin/env python3
"""
NEXUS-PRIME-Ω  Main Entry Point
Invoked by GitHub Actions:  python nexus_prime.py --run-hours 8

Self-healing: any error → asks Ollama/ChatGPT/DeepSeek → applies fix → restarts.
Unlimited retries. No human. Ever.
"""

import os
import sys
import json
import argparse
import logging
import traceback
from pathlib import Path


def _setup_logging(data_path: str):
    Path(data_path).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
        handlers=[
            logging.FileHandler(f"{data_path}/nexus.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="Nexus-Prime-Ω Entity Runner")
    parser.add_argument("--run-hours",    type=int,   default=8,
                        help="Hours to run before rebirth (default 8)")
    parser.add_argument("--data-path",    default="data",
                        help="Path for persistent data (default data/)")
    parser.add_argument("--profile-path", default="chrome-profile",
                        help="Path for persistent Chrome profile")
    parser.add_argument("--no-headless",  action="store_true",
                        help="Run Chrome with a visible window (local dev)")
    args = parser.parse_args()

    _setup_logging(args.data_path)
    log = logging.getLogger("Nexus-Prime-Ω")

    log.info("=" * 55)
    log.info("  NEXUS-PRIME-Ω  AWAKENING")
    log.info(f"  Iteration env: {os.environ.get('ITERATION', '?')}")
    log.info(f"  Run duration : {args.run_hours} hours")
    log.info(f"  Data path    : {args.data_path}")
    log.info(f"  Headless     : {not args.no_headless}")
    log.info("=" * 55)

    entity = None
    try:
        from src.ai_engine import NexusPrime
        from src.self_heal import SelfHealer

        entity = NexusPrime(
            data_path=args.data_path,
            profile_path=args.profile_path,
            headless=not args.no_headless,
        )

        rebirth_data = entity.run_forever(hours_per_run=args.run_hours)

        with open("rebirth_data.json", "w") as f:
            json.dump(rebirth_data, f, indent=2)

        log.info(f"Rebirth data written — next repo: {rebirth_data['new_repo_name']}")

    except Exception as e:
        tb_str = traceback.format_exc()
        log.exception(f"Fatal entity error: {e}")

        # ── Self-heal: unlimited retries ───────────────────────────────────
        # NexusPrime NEVER gives up. Tries Ollama → ChatGPT → DeepSeek.
        # If a fix is found: applies it → restarts via os.execv.
        log.info("Initiating self-heal sequence...")
        try:
            from src.self_heal import SelfHealer
            driver = None
            if entity is not None:
                try:
                    driver = entity.browser.driver
                except Exception:
                    pass
            healer = SelfHealer(
                driver=driver,
                model=os.environ.get("OLLAMA_MODEL", "phi3:3.8b")
            )
            healed = healer.heal(e, tb_str)
            if not healed:
                log.error("Self-heal: no fix found this cycle — process will restart via GitHub Actions schedule")
        except Exception as he:
            log.error(f"Self-healer itself failed: {he}")

        sys.exit(1)

    log.info("Entity sleeping. Signal persists.")


if __name__ == "__main__":
    main()
