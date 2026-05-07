"""
One Piece CG Stock Tracker — Multi-Store
Monitors OP-17 across all major retailers.
Sends Telegram alerts when stock status changes.

SETUP (Railway):
  1. Go to your project -> Variables tab
  2. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
  3. Redeploy — done

SETUP (local):
  1. pip install requests beautifulsoup4
  2. set TELEGRAM_BOT_TOKEN=xxx
     set TELEGRAM_CHAT_ID=yyy
  3. Test:  python op17_tracker.py --test
  4. Run:   python op17_tracker.py
"""

import requests
import time
import logging
import sys
import random
import os
from datetime import datetime

# ── CONFIG ─────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

CHECK_INTERVAL = 5 * 60  # seconds between full cycles (5 min)

# ── STORES ─────────────────────────────────────────────────────────────────────
STORES = [
    # ── Canada ──────────────────────────────────────────────────────────────────
    {
        "name": "Hairy Tarantula",
        "url": "https://hairyt.com/collections/one-piece-cg-sealed-products",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "401 Games",
        "url": "https://store.401games.ca/collections/one-piece",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Level Up Games Canada",
        "url": "https://levelupgames.ca",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "PvP Shoppe",
        "url": "https://www.pvpshoppe.com",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Top Shelf Co.",
        "url": "https://topshelfco.ca",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Doe's Cards",
        "url": "https://doescards.ca",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Game Time Collectibles",
        "url": "https://gametimecollectibles.com",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Three Kingdoms Games",
        "url": "https://threekingdomsgames.com",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Hobbiesville",
        "url": "https://hobbiesville.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "KanZen Games",
        "url": "https://kanzengames.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Meeplemart",
        "url": "https://www.meeplemart.com/one-piece-card-game.aspx",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Deck Out Gaming",
        "url": "https://deckoutgaming.ca/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Face to Face Games",
        "url": "https://www.facetofacegames.com/one-piece",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Magic Stronghold",
        "url": "https://www.magicstronghold.com/store/category/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Carta Magica",
        "url": "https://cartamagica.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Imaginaire",
        "url": "https://imaginaire.com/en/games-and-puzzles/one-piece-card-game.html",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Trinity Hobby",
        "url": "https://trinityhobby.com/collections/one-piece",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "The Connection Games",
        "url": "https://theconnectiongames.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Untouchables",
        "url": "https://untouchables.ca/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Toy Trove",
        "url": "https://toytrove.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Red Riot Games",
        "url": "https://redriotgames.ca/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Banana Games",
        "url": "https://bananagames.ca/products/one-piece-cg-op-17-booster-box",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Rimrock Hobbies",
        "url": "https://rimrockhobbies.com/product/bandai-one-piece-card-game-op-17-booster-box-pre-order/",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Manta Trading",
        "url": "https://mantatrading.com/collections/one-piece",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Torchlight Games",
        "url": "https://torchlightgh.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Skyfox Games",
        "url": "https://skyfoxgames.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Taps Games",
        "url": "https://tapsgames.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Loot Lords",
        "url": "https://www.lootlords.ca/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Grand Line TCG Vancouver",
        "url": "https://grandlinetcgvancouver.ca",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Lotus Petal Gaming",
        "url": "https://lotuspetalgaming.com/collections/one-piece",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Arcadia Collectibles",
        "url": "https://arcadiacollectibles.com",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Flaring Lair",
        "url": "https://flaringlair.ca",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Empire Trading",
        "url": "https://empiretradingco.com",
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
        "name": "NorthlineCards",
        "url": "https://northlinecards.ca",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "EA Collectibles",
        "url": "https://www.eacollectibles.com/collections/one-piece-booster-boxes",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Snapcaster Canada",
        "url": "https://snapcaster.ca",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    # ── USA ─────────────────────────────────────────────────────────────────────
    {
        "name": "Miniature Market",
        "url": "https://www.miniaturemarket.com/One-Piece-TCG-Set-17-OP-17-Booster-Box-24-Preorder/BAN2863367-BOX",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "CardXPlaza",
        "url": "https://www.cardxplaza.com/one-piece-products",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Hypno Comics",
        "url": "https://www.hypnocomics.com/product/one-piece-tcg-op-17-booster-box-pre-order-8-28-2026/FZVYE2EOH4MBGEFKSCGRYTGR",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Gamers Guild AZ",
        "url": "https://gamersguildaz.com",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Zulu's Board Game Cafe",
        "url": "https://zulusgames.com",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Collectors Cache",
        "url": "https://collectorscache.com",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Pro-Play Games",
        "url": "https://pro-playgames.com",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "CoreTCG",
        "url": "https://coretcg.crystalcommerce.com",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "TCGplayer",
        "url": "https://www.tcgplayer.com/search/one-piece-card-game/product?q=op-17",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Amazon Canada",
        "url": "https://www.amazon.ca/s?k=one+piece+op-17+booster+box",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "Amazon USA",
        "url": "https://www.amazon.com/s?k=one+piece+op-17+booster+box",
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
    {
        "name": "Cardmarket",
        "url": "https://www.cardmarket.com/en/OnePiece/Products/Booster-Boxes?searchString=op-17",
        "watch": {"OP-17": ["op-17", "op17"]},
    },
    {
        "name": "OPTCG Market",
        "url": "https://www.optcg.gg/market",
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
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
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
        print("   Railway: Variables tab -> add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID\n")
        return

    print(f"2. Checking {len(STORES)} stores...\n")
    lines = []
    for store in STORES:
        results = check_store(store)
        for product, status in results.items():
            label = "IN STOCK" if status is True else ("PRE-ORDER/SOLD OUT" if status == "preorder" else "not found")
            line = f"  {store['name']} - {product}: {label}"
            print(line)
            lines.append(line)
        time.sleep(1)

    print("\n3. Sending Telegram test message...")
    ok = send_telegram(
        "<b>One Piece Tracker - Test OK!</b>\n\n"
        + "\n".join(lines)
        + f"\n\nChecked {len(STORES)} stores at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print("   Sent! Check your Telegram." if ok else "   FAILED - check token/chat ID.")
    print("\nRun normally with: python op17_tracker.py\n")


def main():
    validate_config()

    log.info("=" * 60)
    log.info(f"One Piece Tracker started - {len(STORES)} stores")
    log.info(f"Checking every {CHECK_INTERVAL // 60} minutes")
    log.info("=" * 60)

    send_telegram(
        "<b>One Piece Tracker running!</b>\n"
        f"Monitoring {len(STORES)} stores for OP-17\n"
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
                        f"ALERT: <b>{product} IN STOCK</b> at <b>{store['name']}</b>!\n"
                        f"<a href='{store['url']}'>Buy now</a>"
                    )

                elif status == "preorder" and prev != "preorder":
                    log.info(f"  {store['name']} | {product}: pre-order listed")
                    alerts.append(
                        f"INFO: <b>{product}</b> listed at <b>{store['name']}</b> (pre-order)\n"
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
                f"<b>Stock Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}</b>\n\n"
                + "\n\n".join(alerts)
            )

        log.info(f"Cycle #{cycle} done. Next in {CHECK_INTERVAL // 60} min.")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_test()
    else:
        main()
