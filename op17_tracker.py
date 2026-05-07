"""
One Piece CG Stock Tracker — Multi-Store
Monitors OP-17 (+ OP-14, OP-15) across all major retailers.
Sends Telegram alerts when stock status changes.

SETUP (local):
  1. pip install requests beautifulsoup4
  2. Set environment variables:
     Windows:   set TELEGRAM_BOT_TOKEN=xxx  &&  set TELEGRAM_CHAT_ID=yyy
     Mac/Linux: export TELEGRAM_BOT_TOKEN=xxx && export TELEGRAM_CHAT_ID=yyy
  3. Test:  python op17_tracker.py --test
  4. Run:   python op17_tracker.py

SETUP (Railway):
  1. Go to your project → Variables tab
  2. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
  3. Redeploy — done
"""

import requests
import time
import logging
import sys
import random
import os
from datetime import datetime

# ── CONFIG — reads from environment variables ──────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

CHECK_INTERVAL = 5 * 60   # seconds between full cycles (5 min)

# ── STORES ─────────────────────────────────────────────────────────────────────
STORES = [
    # ── Canada ──────────────────────────────────────────────────────────────────
    {
        "name": "Hairy Tarantula",
        "url": "https://hairyt.com/collections/one-piece-cg-sealed-products",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Banana Games",
        "url": "https://bananagames.ca/products/one-piece-cg-op-17-booster-box",
        "watch": {"OP-17": ["op-17", "op17", "add to cart"]},
    },
    {
        "name": "Red Riot Games",
        "url": "https://redriotgames.ca/products/one-piece-cg-op-17-pre-orders",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "401 Games",
        "url": "https://store.401games.ca/collections/one-piece-pre-orders",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Hobbiesville",
        "url": "https://hobbiesville.com/products/one-piece-cg-op-17-booster-box-pre-order-copy",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Kanzen Games",
        "url": "https://kanzengames.com/collections/one-piece-pre-order-1",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Game Shack",
        "url": "https://www.gameshack.ca/products/one-piece-op17-bpk",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Miraj Trading",
        "url": "https://www.mirajtrading.com/en-us/products/one-piece-cg-op-17-booster-box-pre-order",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Breakaway Sports Cards",
        "url": "https://breakawaysc.com/product/one-piece-op-17-booster-box/",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Beckett Castle TCG",
        "url": "https://beckettcastletcg.com/",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Rimrock Hobbies",
        "url": "https://rimrockhobbies.com/product/bandai-one-piece-card-game-op-17-booster-box-pre-order/",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    # ── USA ─────────────────────────────────────────────────────────────────────
    {
        "name": "Miniature Market",
        "url": "https://www.miniaturemarket.com/One-Piece-TCG-Set-17-OP-17-Booster-Box-24-Preorder/BAN2863367-BOX",
        "watch": {"OP-17": ["op-17", "op17", "add to cart"]},
    },
    {
        "name": "CardXPlaza",
        "url": "https://www.cardxplaza.com/one-piece-products?page=2",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Hypno Comics",
        "url": "https://www.hypnocomics.com/product/one-piece-tcg-op-17-booster-box-pre-order-8-28-2026/FZVYE2EOH4MBGEFKSCGRYTGR",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    # ── EU ──────────────────────────────────────────────────────────────────────
    {
        "name": "OUPI.eu",
        "url": "https://oupi.eu/en/booster-box-one-piece/7370-op-17-sealed-booster-box-case-english-one-piece-card-game.html",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Zatu Games",
        "url": "https://zatu.com/collections/pre-orders-one-piece",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Chobanov Games",
        "url": "https://chobanovgamesltd.com/product/pre-order-op17-sealed-booster-case-12x-boxes-english-one-piece-card-game.html",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
]

SOLD_OUT_SIGNALS = [
    "sold out", "out of stock", "unavailable",
    "notify me when available", "coming soon",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
]
# ───────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(), logging.FileHandler("op_tracker.log")],
)
log = logging.getLogger(__name__)


def get_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}


def send_telegram(message: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=15)
        r.raise_for_status()
        log.info("Telegram sent OK.")
        return True
    except Exception as e:
        log.error(f"Telegram failed: {e}")
        return False


def fetch_page(url: str):
    try:
        r = requests.get(url, headers=get_headers(), timeout=20)
        r.raise_for_status()
        return r.text.lower()
    except Exception as e:
        log.warning(f"Fetch failed [{url}]: {e}")
        return None


def check_store(store: dict) -> dict:
    results = {}
    page_text = fetch_page(store["url"])
    for product, terms in store["watch"].items():
        if page_text is None:
            results[product] = False
            continue
        found = any(t.lower() in page_text for t in terms)
        if found:
            sold_out = any(s in page_text for s in SOLD_OUT_SIGNALS)
            results[product] = "preorder" if sold_out else True
        else:
            results[product] = False
    return results


def validate_config():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")
    if not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_CHAT_ID environment variable is not set.")


def run_test():
    print("\n=== TEST MODE ===\n")

    print("1. Validating config...")
    try:
        validate_config()
        print("   OK\n")
    except ValueError as e:
        print(f"   ERROR: {e}")
        print("\n   Set your variables first:")
        print("   Railway: Variables tab → add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        print("   Windows: set TELEGRAM_BOT_TOKEN=xxx && set TELEGRAM_CHAT_ID=yyy\n")
        return

    print(f"2. Checking {len(STORES)} stores...\n")
    lines = []
    for store in STORES:
        results = check_store(store)
        for product, status in results.items():
            label = "IN STOCK" if status is True else ("PRE-ORDER/SOLD OUT" if status == "preorder" else "not found")
            line = f"  {store['name']} — {product}: {label}"
            print(line)
            lines.append(line)
        time.sleep(1)

    print("\n3. Sending Telegram test message...")
    msg = (
        "<b>One Piece Tracker — Test OK!</b>\n\n"
        + "\n".join(lines)
        + f"\n\nChecked {len(STORES)} stores at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    ok = send_telegram(msg)
    print("   Sent! Check your Telegram." if ok else "   FAILED — check token/chat ID.")
    print("\nRun normally with: python op17_tracker.py\n")


def main():
    validate_config()

    log.info("=" * 60)
    log.info(f"One Piece Tracker started — {len(STORES)} stores")
    log.info(f"Checking every {CHECK_INTERVAL // 60} minutes")
    log.info("=" * 60)

    send_telegram(
        "<b>One Piece Tracker running!</b>\n"
        f"Monitoring {len(STORES)} stores for OP-14, OP-15, OP-17\n"
        f"Checking every {CHECK_INTERVAL // 60} min"
    )

    previous = {s["name"]: {p: None for p in s["watch"]} for s in STORES}
    cycle = 0

    while True:
        cycle += 1
        log.info(f"--- Cycle #{cycle} ---")
        alerts = []

        for store in STORES:
            results = check_store(store)
            for product, status in results.items():
                prev = previous[store["name"]][product]

                if prev is None:
                    log.info(f"  {store['name']} | {product}: {status} (initial)")
                elif status is True and prev != True:
                    log.info(f"  {store['name']} | {product}: NOW IN STOCK!")
                    alerts.append(
                        f"🚨 <b>{product} IN STOCK</b> at <b>{store['name']}</b>!\n"
                        f"<a href='{store['url']}'>Buy now</a>"
                    )
                elif status == "preorder" and prev != "preorder":
                    log.info(f"  {store['name']} | {product}: pre-order listed")
                    alerts.append(
                        f"📋 <b>{product}</b> listed at <b>{store['name']}</b> (pre-order)\n"
                        f"<a href='{store['url']}'>Check it out</a>"
                    )
                elif status is False and prev is True:
                    log.info(f"  {store['name']} | {product}: went out of stock")
                else:
                    log.info(f"  {store['name']} | {product}: {status} (no change)")

                previous[store["name"]][product] = status
            time.sleep(1)

        if alerts:
            send_telegram(
                f"<b>Stock Alert — {datetime.now().strftime('%Y-%m-%d %H:%M')}</b>\n\n"
                + "\n\n".join(alerts)
            )

        log.info(f"Cycle #{cycle} done. Next in {CHECK_INTERVAL // 60} min.")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_test()
    else:
        main()
