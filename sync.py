#!/usr/bin/env python3
"""
Sarv Rates Engine
=================
Sovereign multi-tier live market price aggregator for Iranian financial assets.
Aggregates official gold & coin indicators (TGJU), domestic exchange order books (Wallex, Nobitex),
and mathematically derives the full Parsian coin series from spot 18k gold.

Author: Suffergod (https://github.com/Suffergod)
License: MIT
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# Plausibility constraints for Iranian economic reality (1404 - 1406)
PLAUSIBILITY_BOUNDS = {
    "usd": (50_000, 1_000_000),
    "usdt": (50_000, 1_000_000),
    "18ayar": (3_000_000, 100_000_000),
    "24ayar": (4_000_000, 150_000_000),
    "abshodeh": (15_000_000, 500_000_000),
    "sekkeh": (30_000_000, 1_000_000_000),
    "bahar": (30_000_000, 1_000_000_000),
    "nim": (15_000_000, 500_000_000),
    "rob": (8_000_000, 300_000_000),
    "gerami": (4_000_000, 150_000_000),
    "silver": (50_000, 5_000_000),
    "btc": (1_000_000_000, 500_000_000_000),
}


def http_get_json(url: str, timeout: int = 10) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[-] Request failed for {url}: {e}", file=sys.stderr)
    return None


def is_plausible(symbol: str, price_tomans: int) -> bool:
    if price_tomans <= 0:
        return False
    if symbol.startswith("parsian_"):
        return 200_000 <= price_tomans <= 250_000_000
    bounds = PLAUSIBILITY_BOUNDS.get(symbol)
    if bounds:
        return bounds[0] <= price_tomans <= bounds[1]
    return True


def fetch_wallex() -> dict[str, dict]:
    """Ingests all 180+ Toman-quoted pairs directly from Wallex domestic exchange."""
    url = "https://api.wallex.ir/v1/markets"
    data = http_get_json(url)
    if not data:
        return {}

    symbols_data = data.get("result", {}).get("symbols", {})
    results = {}

    for pair_key, info in symbols_data.items():
        if not isinstance(info, dict):
            continue

        quote_asset = str(info.get("quoteAsset", "")).upper()
        if quote_asset != "TMN" and not pair_key.endswith("TMN"):
            continue

        base_asset = str(info.get("baseAsset", pair_key.replace("TMN", ""))).lower()
        stats = info.get("stats", {})
        try:
            price_tomans = round(float(stats.get("lastPrice", 0)))
        except (ValueError, TypeError):
            continue

        if price_tomans <= 0:
            continue

        try:
            change_24h = round(float(stats.get("24h_ch", 0)), 2)
        except (ValueError, TypeError):
            change_24h = 0.0

        fa_name = info.get("faName") or info.get("faTitle") or base_asset.upper()
        title_fa = f"{fa_name} ({base_asset.upper()})"

        results[base_asset] = {
            "symbol": base_asset,
            "titleFa": title_fa,
            "priceTomans": price_tomans,
            "changePercentage24h": change_24h,
            "category": "crypto",
            "source": "Wallex",
        }

    # Best Iranian free-market USD benchmark: Tether (USDT)
    if "usdt" in results:
        results["usd"] = {
            "symbol": "usd",
            "titleFa": "دلار آمریکا (آزاد)",
            "priceTomans": results["usdt"]["priceTomans"],
            "changePercentage24h": results["usdt"]["changePercentage24h"],
            "category": "fiat",
            "source": "Wallex (USDT Benchmark)",
        }

    # Paxos Gold (PAXG) physical gold ounce benchmark
    paxg_info = symbols_data.get("PAXGTMN", {})
    if isinstance(paxg_info, dict):
        try:
            paxg_price = float(paxg_info.get("stats", {}).get("lastPrice", 0))
            if paxg_price > 100_000_000:
                # 1 Troy Ounce = 31.1035g of 24k gold. Gram of 18k = (Price / 31.1035) * (18/24)
                gold18_derived = round((paxg_price / 31.1035) * 0.75)
                results["18ayar_paxg"] = {
                    "symbol": "18ayar",
                    "titleFa": "طلای ۱۸ عیار (هر گرم)",
                    "priceTomans": gold18_derived,
                    "changePercentage24h": 0.0,
                    "category": "gold",
                    "source": "Wallex (Paxos Gold)",
                }
        except (ValueError, TypeError):
            pass

    return results


def fetch_tgju() -> dict[str, dict]:
    """Ingests official 31 indicators from Tehran Gold & Jewelry Union (TGJU)."""
    keys = (
        "geram18,geram24,mesghal,ons,silver,sekee,sekeb,nim,rob,gerami,"
        "price_dollar_rl,price_eur,price_gbp,price_aed,price_try,price_cad,price_aud,price_cny,"
        "price_kwd,price_iqd,price_sar,price_chf,price_jpy,price_inr,price_pkr,price_omr,"
        "price_qar,price_rub,price_azn,price_amd,price_gel"
    )
    url = f"https://api.tgju.org/v1/widget/tmp?keys={keys}"
    data = http_get_json(url)
    if not data:
        return {}

    indicators = data.get("response", {}).get("indicators", [])
    mappings = {
        "geram18": ("18ayar", "طلای ۱۸ عیار (هر گرم)", "gold"),
        "geram24": ("24ayar", "طلای ۲۴ عیار (هر گرم)", "gold"),
        "mesghal": ("abshodeh", "طلای آب‌شده (مثقال)", "gold"),
        "ons": ("ons", "انس جهانی طلا (دلار)", "gold"),
        "silver": ("silver", "نقره خام (هر گرم)", "gold"),
        "sekee": ("sekkeh", "سکه تمام بهار آزادی (امامی)", "gold"),
        "sekeb": ("bahar", "سکه بهار آزادی (طرح قدیم)", "gold"),
        "nim": ("nim", "نیم سکه بهار آزادی", "gold"),
        "rob": ("rob", "ربع سکه بهار آزادی", "gold"),
        "gerami": ("gerami", "سکه گرمی", "gold"),
        "price_dollar_rl": ("usd", "دلار آمریکا (آزاد)", "fiat"),
        "price_eur": ("eur", "یورو اروپا", "fiat"),
        "price_gbp": ("gbp", "پوند انگلیس", "fiat"),
        "price_aed": ("aed", "درهم امارات", "fiat"),
        "price_try": ("try", "لیر ترکیه", "fiat"),
        "price_cad": ("cad", "دلار کانادا", "fiat"),
        "price_aud": ("aud", "دلار استرالیا", "fiat"),
        "price_cny": ("cny", "یوان چین", "fiat"),
        "price_kwd": ("kwd", "دینار کویت", "fiat"),
        "price_iqd": ("iqd", "صد دینار عراق", "fiat"),
        "price_sar": ("sar", "ریال عربستان", "fiat"),
        "price_chf": ("chf", "فرانک سوئیس", "fiat"),
        "price_jpy": ("jpy", "صد ین ژاپن", "fiat"),
        "price_inr": ("inr", "روپیه هند", "fiat"),
        "price_pkr": ("pkr", "روپیه پاکستان", "fiat"),
        "price_omr": ("omr", "ریال عمان", "fiat"),
        "price_qar": ("qar", "ریال قطر", "fiat"),
        "price_rub": ("rub", "روبل روسیه", "fiat"),
        "price_azn": ("azn", "منات آذربایجان", "fiat"),
        "price_amd": ("amd", "درام ارمنستان", "fiat"),
        "price_gel": ("gel", "لاری گرجستان", "fiat"),
    }

    results = {}
    for ind in indicators:
        name = str(ind.get("name", ""))
        mapping = mappings.get(name)
        if not mapping:
            continue

        raw_p = str(ind.get("p", "")).replace(",", "").replace("٬", "")
        try:
            val = float(raw_p)
            if val <= 0:
                continue
            # TGJU prices are in Rials (except ons which is in USD)
            price_tomans = round(val) if mapping[0] == "ons" else round(val / 10)
        except (ValueError, TypeError):
            continue

        try:
            change_pct = round(float(ind.get("dp", 0)), 2)
        except (ValueError, TypeError):
            change_pct = 0.0

        results[mapping[0]] = {
            "symbol": mapping[0],
            "titleFa": mapping[1],
            "priceTomans": price_tomans,
            "changePercentage24h": change_pct,
            "category": mapping[2],
            "source": "TGJU",
        }

    return results


def fetch_nobitex() -> dict[str, dict]:
    """Ingests domestic crypto prices from Nobitex as secondary fallback."""
    url = "https://apiv2.nobitex.ir/market/stats"
    data = http_get_json(url)
    if not data:
        return {}

    stats = data.get("stats", {})
    results = {}

    pairs = {
        "usdt-rls": ("usdt", "تتر (USDT)", "crypto"),
        "btc-rls": ("btc", "بیت‌کوین (BTC)", "crypto"),
        "eth-rls": ("eth", "اتریوم (ETH)", "crypto"),
        "trx-rls": ("trx", "ترون (TRX)", "crypto"),
        "sol-rls": ("sol", "سولانا (SOL)", "crypto"),
    }

    for pair_key, mapping in pairs.items():
        pair_info = stats.get(pair_key, {})
        if not isinstance(pair_info, dict):
            continue
        try:
            latest_rls = float(pair_info.get("latest", 0))
            if latest_rls <= 0:
                continue
            price_tomans = round(latest_rls / 10)
            day_change = round(float(pair_info.get("dayChange", 0)), 2)
            results[mapping[0]] = {
                "symbol": mapping[0],
                "titleFa": mapping[1],
                "priceTomans": price_tomans,
                "changePercentage24h": day_change,
                "category": mapping[2],
                "source": "Nobitex",
            }
        except (ValueError, TypeError):
            continue

    return results


def derive_parsian_coins(rates: dict[str, dict]) -> None:
    """Derives all 13 standard Parsian coin denominations from the spot 18k gold price."""
    gold18 = rates.get("18ayar")
    if not gold18 or gold18.get("priceTomans", 0) <= 0:
        return

    price_18k = gold18["priceTomans"]
    packaging_fee = 60_000  # 60,000 Tomans minting and sealing fee

    parsian_series = [
        (100, 0.100, "سکه پارسیان ۱۰۰ سوت"),
        (200, 0.200, "سکه پارسیان ۲۰۰ سوت"),
        (300, 0.300, "سکه پارسیان ۳۰۰ سوت"),
        (400, 0.400, "سکه پارسیان ۴۰۰ سوت"),
        (500, 0.500, "سکه پارسیان ۵۰۰ سوت (نیم گرم)"),
        (600, 0.600, "سکه پارسیان ۶۰۰ سوت"),
        (700, 0.700, "سکه پارسیان ۷۰۰ سوت"),
        (800, 0.800, "سکه پارسیان ۸۰۰ سوت"),
        (900, 0.900, "سکه پارسیان ۹۰۰ سوت"),
        (1000, 1.000, "سکه پارسیان ۱ گرمی (۱۰۰۰ سوت)"),
        (1200, 1.200, "سکه پارسیان ۱.۲ گرمی"),
        (1500, 1.500, "سکه پارسیان ۱.۵ گرمی"),
        (2000, 2.000, "سکه پارسیان ۲ گرمی"),
    ]

    for soot, weight_grams, title in parsian_series:
        symbol = f"parsian_{soot}"
        coin_price = round(weight_grams * price_18k) + packaging_fee
        rates[symbol] = {
            "symbol": symbol,
            "titleFa": title,
            "priceTomans": coin_price,
            "changePercentage24h": gold18.get("changePercentage24h", 0.0),
            "category": "gold",
            "source": "Formula Derived (Spot 18k Gold)",
        }


def main():
    print(f"[*] Starting Sarv Rates Ingestion Engine @ {datetime.now(timezone.utc).isoformat()}")

    aggregated: dict[str, dict] = {}

    # Tier 1: Wallex (Direct domestic exchange)
    wallex_rates = fetch_wallex()
    print(f"[+] Ingested {len(wallex_rates)} pairs from Wallex")
    aggregated.update(wallex_rates)

    # Tier 2: TGJU Widget (Official Tehran gold union indicators)
    tgju_rates = fetch_tgju()
    print(f"[+] Ingested {len(tgju_rates)} indicators from TGJU")
    aggregated.update(tgju_rates)

    # Tier 3: Nobitex (Backup domestic crypto)
    if "usdt" not in aggregated or "btc" not in aggregated:
        nobitex_rates = fetch_nobitex()
        print(f"[+] Ingested {len(nobitex_rates)} backup rates from Nobitex")
        for k, v in nobitex_rates.items():
            if k not in aggregated:
                aggregated[k] = v

    # Fallback for 18k gold if TGJU was offline: use Paxos Gold
    if "18ayar" not in aggregated and "18ayar_paxg" in aggregated:
        aggregated["18ayar"] = aggregated["18ayar_paxg"]
    aggregated.pop("18ayar_paxg", None)

    # Tier 4: Parsian Coins Mathematical Engine
    derive_parsian_coins(aggregated)
    print(f"[+] Derived Parsian coin series from spot 18k rate")

    # Tier 5: Anomaly Gate & Plausibility Validation
    validated: dict[str, dict] = {}
    rejected_count = 0
    for symbol, item in aggregated.items():
        price = item.get("priceTomans", 0)
        if is_plausible(symbol, price):
            validated[symbol] = item
        else:
            rejected_count += 1
            print(f"[!] Plausibility gate rejected: {symbol} = {price}")

    if not validated:
        print("[!] ERROR: No valid rates survived plausibility gate. Aborting.", file=sys.stderr)
        sys.exit(1)

    print(f"[+] Validated {len(validated)} sovereign rates (Rejected anomalies: {rejected_count})")

    # Sort priority
    priority = [
        "18ayar", "24ayar", "sekkeh", "bahar", "nim", "rob", "gerami", "abshodeh", "silver",
        "usd", "usdt", "eur", "gbp", "aed", "try", "cad", "aud", "cny", "kwd", "iqd",
        "btc", "eth", "sol", "ton", "trx", "doge", "ada", "xrp"
    ]

    def sort_key(item: dict) -> tuple[int, str]:
        sym = item["symbol"]
        try:
            return (priority.index(sym), sym)
        except ValueError:
            cat_order = {"gold": 100, "fiat": 200, "crypto": 300}.get(item["category"], 400)
            return (cat_order, sym)

    sorted_list = sorted(validated.values(), key=sort_key)

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    timestamp = int(time.time())
    iso_time = datetime.now(timezone.utc).isoformat()

    # 1. Full unified rates dictionary
    output_full = {
        "metadata": {
            "name": "Sarv Rates API",
            "version": "1.0",
            "updatedAt": iso_time,
            "timestamp": timestamp,
            "count": len(sorted_list),
            "sources": ["Wallex API", "TGJU Widget API", "Nobitex API", "Parsian Valuation Engine"],
        },
        "rates": validated,
        "items": sorted_list,
    }

    rates_path = os.path.join(data_dir, "rates.json")
    with open(rates_path, "w", encoding="utf-8") as f:
        json.dump(output_full, f, ensure_ascii=False, indent=2)

    # 2. Ultra-compact format for low-bandwidth mobile devices (short keys)
    compact_path = os.path.join(data_dir, "rates_compact.json")
    compact_output = {
        "updatedAt": iso_time,
        "items": [
            {
                "s": item["symbol"],
                "t": item["titleFa"],
                "p": item["priceTomans"],
                "c": item.get("changePercentage24h", 0.0),
                "cat": item["category"],
            }
            for item in sorted_list
        ],
    }
    with open(compact_path, "w", encoding="utf-8") as f:
        json.dump(compact_output, f, ensure_ascii=False, separators=(",", ":"))

    # 3. Categorized files for granular consumption
    gold_items = [i for i in sorted_list if i["category"] == "gold"]
    fiat_items = [i for i in sorted_list if i["category"] == "fiat"]
    crypto_items = [i for i in sorted_list if i["category"] == "crypto"]

    for name, items in [("gold.json", gold_items), ("fiat.json", fiat_items), ("crypto.json", crypto_items)]:
        p = os.path.join(data_dir, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"updatedAt": iso_time, "count": len(items), "items": items}, f, ensure_ascii=False, indent=2)

    print(f"[+] Output written to {data_dir}:")
    print(f"    - rates.json ({os.path.getsize(rates_path)} bytes)")
    print(f"    - rates_compact.json ({os.path.getsize(compact_path)} bytes)")
    print(f"    - gold.json ({len(gold_items)} items)")
    print(f"    - fiat.json ({len(fiat_items)} items)")
    print(f"    - crypto.json ({len(crypto_items)} items)")


if __name__ == "__main__":
    main()
