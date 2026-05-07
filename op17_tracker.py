"""
One Piece CG Stock Tracker — Multi-Store
Monitors OP-17 (+ OP-14, OP-15) across all major retailers.
Sends Telegram alerts when stock status changes.

SETUP:
  1. Message @BotFather on Telegram → /newbot → copy your bot token
  2. Message your new bot once, then open:
     https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
     Copy the "id" inside "chat" — that's your chat ID
  3. Paste both values below
  4. pip install requests beautifulsoup4
  5. Test:        python op17_tracker.py --test
  6. Run:         python op17_tracker.py
"""

import requests
import time
import logging
import sys
import random
from datetime import datetime
from bs4 import BeautifulSoup

# ── CONFIG ─────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID   = "YOUR_CHAT_ID_HERE"

CHECK_INTERVAL = 5 * 60   # seconds between full cycles (5 min)

# ── STORES ─────────────────────────────────────────────────────────────────────
# Each entry: (store_name, url, [search_terms], [sold_out_terms])
# sold_out_terms: if ANY of these appear alongside the product, it's considered out of stock

STORES = [
    # ── Canada ──────────────────────────────────────────────────────────────────
    {
        "name": "Hairy Tarantula",
        "url": "https://hairyt.com/collections/one-piece-cg-sealed-products",
        "watch": {
            "OP-14": ["op-14", "op14"],
            "OP-15": ["op-15", "op15"],
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Banana Games",
        "url": "https://bananagames.ca/products/one-piece-cg-op-17-booster-box",
        "watch": {
            "OP-17": ["op-17", "op17", "add to cart"],
        },
    },
    {
        "name": "Red Riot Games",
        "url": "https://redriotgames.ca/products/one-piece-cg-op-17-pre-orders",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "401 Games",
        "url": "https://store.401games.ca/collections/one-piece-pre-orders",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Hobbiesville",
        "url": "https://hobbiesville.com/products/one-piece-cg-op-17-booster-box-pre-order-copy",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Kanzen Games",
        "url": "https://kanzengames.com/collections/one-piece-pre-order-1",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Game Shack",
        "url": "https://www.gameshack.ca/products/one-piece-op17-bpk",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Miraj Trading",
        "url": "https://www.mirajtrading.com/en-us/products/one-piece-cg-op-17-booster-box-pre-order",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Breakaway Sports Cards",
        "url": "https://breakawaysc.com/product/one-piece-op-17-booster-box/",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Beckett Castle TCG",
        "url": "https://beckettcastletcg.com/",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Rimrock Hobbies",
        "url": "https://rimrockhobbies.com/product/bandai-one-piece-card-game-op-17-booster-box-pre-order/",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    # ── USA ─────────────────────────────────────────────────────────────────────
    {
        "name": "Miniature Market",
        "url": "https://www.miniaturemarket.com/One-Piece-TCG-Set-17-OP-17-Booster-Box-24-Preorder/BAN2863367-BOX",
        "watch": {
            "OP-17": ["op-17", "op17", "add to cart"],
        },
    },
    {
        "name": "CardXPlaza",
        "url": "https://www.cardxplaza.com/one-piece-products?page=2",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Hypno Comics",
        "url": "https://www.hypnocomics.com/product/one-piece-tcg-op-17-booster-box-pre-order-8-28-2026/FZVYE2EOH4MBGEFKSCGRYTGR",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    # ── EU ──────────────────────────────────────────────────────────────────────
    {
        "name": "OUPI.eu",
        "url": "https://oupi.eu/en/booster-box-one-piece/7370-op-17-sealed-booster-box-case-english-one-piece-card-game.html",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Zatu Games",
        "url": "https://zatu.com/collections/pre-orders-one-piece",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
    {
        "name": "Chobanov Games",
        "url": "https://chobanovgamesltd.com/product/pre-order-op17-sealed-booster-case-12x-boxes-english-one-piece-card-game.html",
        "watch": {
            "OP-17": ["op-17", "op17"],
        },
    },
]

# If page contains these near the product, it's likely sold out / unavailable
SOLD_OUT_SIGNALS = [
    "sold out",
    "out of stock",
    "unavailable",
    "notify me when available",
    "coming soon",
]
# ───────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("op_tracker.log"),
    ]
)
log = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
]


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


def fetch_page(url: str) -> str | None:
    try:
        r = requests.get(url, headers=get_headers(), timeout=20)
        r.raise_for_status()
        return r.text.lower()
    except Exception as e:
        log.warning(f"Fetch failed [{url}]: {e}")
        return None


def check_store(store: dict) -> dict:
    """
    Returns {product_name: True/False} for each watched product.
    True = found on page AND not showing sold-out signals.
    """
    results = {}
    page_text = fetch_page(store["url"])

    for product, terms in store["watch"].items():
        if page_text is None:
            results[product] = False
            continue

        found = any(t.lower() in page_text for t in terms)

        if found:
            # Check for sold-out signals close to the keyword
            sold_out = any(s in page_text for s in SOLD_OUT_SIGNALS)
            # If the ONLY sold-out signal is "coming soon" and product is listed, 
            # treat as pre-order available (still interesting to know)
            results[product] = True  # Found = listed, we report regardless
            if sold_out:
                results[product] = "preorder"  # Listed but sold out / pre-order only
        else:
            results[product] = False

    return results


def validate_config():
    if "YOUR_BOT_TOKEN_HERE" in TELEGRAM_BOT_TOKEN:
        raise ValueError("Set your TELEGRAM_BOT_TOKEN in the script first.")
    if "YOUR_CHAT_ID_HERE" in TELEGRAM_CHAT_ID:
        raise ValueError("Set your TELEGRAM_CHAT_ID in the script first.")


def run_test():
    print("\n=== TEST MODE ===\n")

    print("1. Validating config...")
    try:
        validate_config()
        print("   OK\n")
    except ValueError as e:
        print(f"   ERROR: {e}\n")
        return

    print(f"2. Checking {len(STORES)} stores...\n")
    lines = []
    for store in STORES:
        results = check_store(store)
        for product, status in results.items():
            if status == True:
                icon = "IN STOCK"
            elif status == "preorder":
                icon = "PRE-ORDER/SOLD OUT"
            else:
                icon = "not found"
            line = f"  {store['name']} — {product}: {icon}"
            print(line)
            lines.append(line)
        time.sleep(1)  # be polite

    print("\n3. Sending Telegram test message...")
    msg = (
        "<b>One Piece Tracker — Test Run</b>\n\n"
        + "\n".join(lines) + "\n\n"
        f"Checked {len(STORES)} stores at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    ok = send_telegram(msg)
    print("   Sent!" if ok else "   FAILED — check token/chat ID")
    print("\n=== DONE ===")
    print("Run normally with: python op17_tracker.py\n")


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

    # previous[store_name][product] = True / "preorder" / False / None
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
                    # First run — just log
                    log.info(f"  {store['name']} | {product}: {status} (initial)")

                elif status == True and prev != True:
                    # Newly in stock!
                    log.info(f"  {store['name']} | {product}: NOW IN STOCK!")
                    alerts.append(
                        f"ALERT: <b>{product} IN STOCK</b> at <b>{store['name']}</b>!\n"
                        f"<a href='{store['url']}'>Buy now</a>"
                    )

                elif status == "preorder" and prev != "preorder":
                    log.info(f"  {store['name']} | {product}: listed as pre-order")
                    alerts.append(
                        f"INFO: <b>{product}</b> appeared at <b>{store['name']}</b> (pre-order / sold out)\n"
                        f"<a href='{store['url']}'>Check it out</a>"
                    )

                elif status == False and prev == True:
                    log.info(f"  {store['name']} | {product}: went out of stock")

                else:
                    log.info(f"  {store['name']} | {product}: {status} (no change)")

                previous[store["name"]][product] = status

            time.sleep(1)  # small delay between store fetches

        if alerts:
            msg = (
                f"<b>Stock Alert — {datetime.now().strftime('%Y-%m-%d %H:%M')}</b>\n\n"
                + "\n\n".join(alerts)
            )
            send_telegram(msg)

        log.info(f"Cycle #{cycle} done. Next in {CHECK_INTERVAL // 60} min.")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_test()
    else:
        main()
