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
  3. Test:   python op17_tracker.py --test
  4. Run:    python op17_tracker.py
"""

import requests
import time
import logging
import sys
import random
import os
from datetime import datetime
from bs4 import BeautifulSoup

# ── CONFIG ─────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

CHECK_INTERVAL = 3 * 60  # seconds between full cycles (3 min)

# ── STORES ─────────────────────────────────────────────────────────────────────
STORES = [
    # ── Canada ──────────────────────────────────────────────────────────────────
    {
        "name": "Hairy Tarantula",
        "url": "https://hairyt.com/collections/one-piece-cg-sealed-products",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "401 Games",
        "url": "https://store.401games.ca/collections/one-piece",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Level Up Games Canada",
        "url": "https://levelupgames.ca",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "PvP Shoppe",
        "url": "https://www.pvpshoppe.com",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Top Shelf Co.",
        "url": "https://topshelfco.ca",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Doe's Cards",
        "url": "https://doescards.ca",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Game Time Collectibles",
        "url": "https://gametimecollectibles.com",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Three Kingdoms Games",
        "url": "https://threekingdomsgames.com",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Hobbiesville",
        "url": "https://hobbiesville.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "KanZen Games",
        "url": "https://kanzengames.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Meeplemart",
        "url": "https://www.meeplemart.com/one-piece-card-game.aspx",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Deck Out Gaming",
        "url": "https://deckoutgaming.ca/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Face to Face Games",
        "url": "https://www.facetofacegames.com/one-piece",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Magic Stronghold",
        "url": "https://www.magicstronghold.com/store/category/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Carta Magica",
        "url": "https://cartamagica.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Imaginaire",
        "url": "https://imaginaire.com/en/games-and-puzzles/one-piece-card-game.html",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Trinity Hobby",
        "url": "https://trinityhobby.com/collections/one-piece",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "The Connection Games",
        "url": "https://theconnectiongames.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Untouchables",
        "url": "https://untouchables.ca/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Toy Trove",
        "url": "https://toytrove.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Red Riot Games",
        "url": "https://redriotgames.ca/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Banana Games",
        "url": "https://bananagames.ca/products/one-piece-cg-op-17-booster-box",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Rimrock Hobbies",
        "url": "https://rimrockhobbies.com/product/bandai-one-piece-card-game-op-17-booster-box-pre-order/",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Manta Trading",
        "url": "https://mantatrading.com/collections/one-piece",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Torchlight Games",
        "url": "https://torchlightgh.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Skyfox Games",
        "url": "https://skyfoxgames.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Taps Games",
        "url": "https://tapsgames.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Loot Lords",
        "url": "https://www.lootlords.ca/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Grand Line TCG Vancouver",
        "url": "https://grandlinetcgvancouver.ca",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Lotus Petal Gaming",
        "url": "https://lotuspetalgaming.com/collections/one-piece",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Arcadia Collectibles",
        "url": "https://arcadiacollectibles.com",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Flaring Lair",
        "url": "https://flaringlair.ca",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Empire Trading",
        "url": "https://empiretradingco.com",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Game Shack",
        "url": "https://www.gameshack.ca/products/one-piece-op17-bpk",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Miraj Trading",
        "url": "https://www.mirajtrading.com/en-us/products/one-piece-cg-op-17-booster-box-pre-order",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Breakaway Sports Cards",
        "url": "https://breakawaysc.com/product/one-piece-op-17-booster-box/",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Beckett Castle TCG",
        "url": "https://beckettcastletcg.com/",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "NorthlineCards",
        "url": "https://northlinecards.ca",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "EA Collectibles",
        "url": "https://www.eacollectibles.com/collections/one-piece-booster-boxes",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Snapcaster Canada",
        "url": "https://snapcaster.ca",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    # ── USA ─────────────────────────────────────────────────────────────────────
    {
        "name": "Miniature Market",
        "url": "https://www.miniaturemarket.com/One-Piece-TCG-Set-17-OP-17-Booster-Box-24-Preorder/BAN2863367-BOX",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "CardXPlaza",
        "url": "https://www.cardxplaza.com/one-piece-products",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Hypno Comics",
        "url": "https://www.hypnocomics.com/product/one-piece-tcg-op-17-booster-box-pre-order-8-28-2026/FZVYE2EOH4MBGEFKSCGRYTGR",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Gamers Guild AZ",
        "url": "https://gamersguildaz.com",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Zulu's Board Game Cafe",
        "url": "https://zulusgames.com",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Collectors Cache",
        "url": "https://collectorscache.com",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Pro-Play Games",
        "url": "https://pro-playgames.com",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "CoreTCG",
        "url": "https://coretcg.crystalcommerce.com",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "TCGplayer",
        "url": "https://www.tcgplayer.com/search/one-piece-card-game/product?q=op-17",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Amazon Canada",
        "url": "https://www.amazon.ca/s?k=one+piece+op-17+booster+box",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Amazon USA",
        "url": "https://www.amazon.com/s?k=one+piece+op-17+booster+box",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    # ── EU ──────────────────────────────────────────────────────────────────────
    {
        "name": "OUPI.eu",
        "url": "https://oupi.eu/en/booster-box-one-piece/7370-op-17-sealed-booster-box-case-english-one-piece-card-game.html",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Zatu Games",
        "url": "https://zatu.com/collections/pre-orders-one-piece",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Chobanov Games",
        "url": "https://chobanovgamesltd.com/product/pre-order-op17-sealed-booster-case-12x-boxes-english-one-piece-card-game.html",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Cardmarket",
        "url": "https://www.cardmarket.com/en/OnePiece/Products/Booster-Boxes?searchString=op-17",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "OPTCG Market",
        "url": "https://www.optcg.gg/market",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    # ── Chinese / Asian Stores (ship to Canada) ──────────────────────────────
    {
        "name": "TCGHobby (Taiwan) ✅",
        "url": "https://www.tcghobby.com/collections/one-piece",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Exp. Share Collectible (US/Chinese) ✅",
        "url": "https://escollectible.com/pages/chinese-one-piece-tcg",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Ninoma (EU/Asian TCG) ✅",
        "url": "https://ninoma.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Otaku Asia (Asian TCG ships worldwide) ✅",
        "url": "https://www.otakuasia.com/collections/one-piece-card-game",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set", "op-anniversary", "3rd-anniversary"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary", "anniversary set chinese", "op-4th"]},
    },
    {
        "name": "Buyee Japan Proxy ✅",
        "url": "https://buyee.jp/item/search/query/one+piece+op-17+booster+box",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary"]},
    },
    {
        "name": "YYT (Asia TCG) ✅",
        "url": "https://www.yyt.com/en/one-piece",
        "watch": {"OP-17": ["op-17", "op17"], "3rd Anniversary Set": ["3rd anniversary", "anniversary set"], "4th Anniversary Set (Chinese)": ["4th anniversary", "4th-anniversary", "chinese anniversary"]},
    },
]

SOLD_OUT_SIGNALS = ["sold out", "out of stock", "unavailable"]
BUY_SIGNALS = ["add to cart", "pre-order", "preorder", "pre order", "buy now", "order now", "reserve now", "add to bag"]
FALSE_POSITIVE_SIGNALS = ["coming soon", "notify me", "notify me when available", "email me when available", "out of stock", "sold out", "unavailable"]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
]

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

def fetch_all_pages(base_url: str) -> str:
    all_text = ""
    page_num = 1
    last_text = None
    separator = "&" if "?" in base_url else "?"

    while page_num <= 5:  # Dropped cap to 5 to protect execution speeds/IP bans
        url = base_url if page_num == 1 else f"{base_url}{separator}page={page_num}"
        text = fetch_page(url)

        if text is None or text == last_text:
            break
        if page_num > 1 and len(text.strip()) < 500:
            break

        all_text += text
        last_text = text
        page_num += 1
        time.sleep(1.0)  # Politeness margin

    return all_text

def check_store(store: dict) -> dict:
    results = {}
    page_html = fetch_all_pages(store["url"])
    if not page_html:
        return {prod: False for prod in store["watch"]}

    soup = BeautifulSoup(page_html, 'html.parser')
    
    # Locate all distinct product containers (covers Shopify, WooCommerce, and standard grids)
    containers = soup.find_all(['div', 'li', 'article', 'tr'])

    for product, terms in store["watch"].items():
        results[product] = False
        product_blocks = []

        # Isolate blocks containing our target product terms
        for node in containers:
            node_text = node.get_text().lower()
            if any(term.lower() in node_text for term in terms):
                # Ensure we capture parent card element, not just a deeply nested span
                if node.name in ['div', 'li', 'article', 'tr'] and len(node_text) < 2000:
                    product_blocks.append(node_text)

        # Fallback to absolute document text if structural block parsing finds nothing
        if not product_blocks:
            if any(term.lower() in page_html for term in terms):
                product_blocks.append(page_html)

        # Contextually evaluate isolated product snippets
        for block in product_blocks:
            has_buy_button = any(b in block for b in BUY_SIGNALS)
            is_sold_out = any(s in block for s in SOLD_OUT_SIGNALS)
            is_preorder = any(p in block for p in ["pre-order", "preorder", "pre order"])
            is_false_pos = any(f in block for f in FALSE_POSITIVE_SIGNALS) and not has_buy_button

            if is_false_pos or (is_sold_out and not is_preorder and not has_buy_button):
                continue

            if is_preorder and has_buy_button:
                results[product] = "preorder"
                break
            elif has_buy_button:
                results[product] = True
                break
                
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
            label = "IN STOCK" if status is True else ("PRE-ORDER" if status == "preorder" else "not found/sold out")
            line = f"  {store['name']} - {product}: {label}"
            print(line)
            lines.append(line)
        time.sleep(1)

    print("\n3. Sending Telegram test message...")
    status_summary = "\n".join(lines)
    ok = send_telegram(
        f"<b>One Piece Tracker - Test OK!</b>\n\n"
        f"{status_summary}\n\n"
        f"Checked {len(STORES)} stores successfully."
    )
    if ok:
        print("Test Complete. Telegram notification successfully pushed.")

def main():
    if "--test" in sys.argv:
        run_test()
        return

    try:
        validate_config()
    except ValueError as e:
        log.error(e)
        sys.exit(1)

    log.info("Starting production tracking loop...")
    history = {}  # Tracks previous state to avoid repeat alerts

    while True:
        log.info("Starting collection scan...")
        for store in STORES:
            store_name = store["name"]
            results = check_store(store)

            for product, current_status in results.items():
                history_key = f"{store_name}_{product}"
                previous_status = history.get(history_key, "initial_none")

                # State change detection
                if current_status != previous_status:
                    if previous_status != "initial_none": # Skip announcing baseline states on boot
                        status_text = "🟢 IN STOCK" if current_status is True else ("🟡 PRE-ORDER OPEN" if current_status == "preorder" else "🔴 SOLD OUT")
                        msg = (
                            f"🚨 <b>Stock Change Alert!</b>\n\n"
                            f"<b>Store:</b> {store_name}\n"
                            f"<b>Product:</b> {product}\n"
                            f"<b>New Status:</b> {status_text}\n\n"
                            f"🔗 <a href='{store['url']}'>Link to Store Collection</a>"
                        )
                        send_telegram(msg)
                    history[history_key] = current_status

            time.sleep(random.uniform(1.5, 3.0))  # Anti-throttling cadence delays

        log.info(f"Scan complete. Resting for {CHECK_INTERVAL // 60} minutes...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
