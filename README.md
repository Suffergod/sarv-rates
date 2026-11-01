# Sarv Rates (سرو رِیتس) 🌲

> **Sovereign Real-Time Market Rates API for Iranian Financial Assets**  
> Free, open, and reliable JSON API for Gold, Coins, Parsian Coins, World Fiat Currencies, and Cryptocurrencies quoted in Iranian Tomans.

Updated automatically every 15 minutes via GitHub Actions.

---

## 🚀 Endpoints (Raw JSON)

All endpoints return UTF-8 JSON and can be consumed directly from web apps, mobile apps (Flutter, React Native), or backend services.

| Endpoint | Description | Size |
| :--- | :--- | :--- |
| **[`/data/rates.json`](https://raw.githubusercontent.com/Suffergod/sarv-rates/main/data/rates.json)** | Complete unified dataset (Gold, Fiat, Crypto, Parsian) | ~85 KB |
| **[`/data/rates_compact.json`](https://raw.githubusercontent.com/Suffergod/sarv-rates/main/data/rates_compact.json)** | Minified array payload optimized for low-bandwidth mobile devices | ~17 KB |
| **[`/data/gold.json`](https://raw.githubusercontent.com/Suffergod/sarv-rates/main/data/gold.json)** | 18k, 24k, Melted Gold, Ounce, Silver, Emami, Bahar, Nim, Rob, Gerami + 13 Parsian denominations | ~8 KB |
| **[`/data/fiat.json`](https://raw.githubusercontent.com/Suffergod/sarv-rates/main/data/fiat.json)** | 21 World Fiat Currencies (USD, EUR, GBP, AED, TRY, CAD, AUD, CNY, KWD, IQD, etc.) | ~6 KB |
| **[`/data/crypto.json`](https://raw.githubusercontent.com/Suffergod/sarv-rates/main/data/crypto.json)** | 150+ Cryptocurrencies quoted in Tomans (USDT, BTC, ETH, SOL, TON, TRX, etc.) | ~70 KB |

---

## 📊 Coverage & Features

- **Gold & Coins (طلا و مسکوکات):**
  - طلای ۱۸ عیار، طلای ۲۴ عیار، مثقال آب‌شده، انس جهانی، نقره خام
  - سکه امامی (تمام بهار آزادی)، سکه بهار آزادی طرح قدیم، نیم‌سکه، ربع‌سکه، سکه گرمی
  - **سلسله کامل سکه‌های پارسیان (۱۳ رده):** از ۱۰۰ سوت تا ۲۰۰۰ سوت (۲ گرم) با فرمول استاندارد مظنه روز و حباب ساخت
- **World Currencies (ارزهای بین‌المللی):**
  - ۲۱ ارز معتبر جهانی به ریال و تومان (دلار آزاد، تتر، یورو، پوند، درهم امارات، لیر ترکیه، دینار کویت، صد دینار عراق، روبل و...)
- **Cryptocurrencies (رمزارزها به تومان):**
  - بیش از ۱۵۰ جفت‌ارز تتری و تومانی مستقیم از اوردربوک صرافی‌های معتبر داخلی
- **Strict Plausibility Gate:**
  - فیلتر خودکار ارقام غیرواقعی، صفر، پکت‌های خراب و خطاهای مقطعی شبکه

---

## 💻 Quick Start

### cURL
```bash
# Get all rates
curl -s https://raw.githubusercontent.com/Suffergod/sarv-rates/main/data/rates.json | jq .
```

### JavaScript / TypeScript
```javascript
const res = await fetch('https://raw.githubusercontent.com/Suffergod/sarv-rates/main/data/rates.json');
const data = await res.json();

console.log('Gold 18k:', data.rates['18ayar'].priceTomans);
console.log('USD:', data.rates['usd'].priceTomans);
console.log('Tether:', data.rates['usdt'].priceTomans);
console.log('Bitcoin:', data.rates['btc'].priceTomans);
```

### Dart / Flutter
```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

Future<void> fetchRates() async {
  final url = Uri.parse('https://raw.githubusercontent.com/Suffergod/sarv-rates/main/data/rates.json');
  final res = await http.get(url);
  if (res.statusCode == 200) {
    final data = jsonDecode(res.body);
    final gold18 = data['rates']['18ayar']['priceTomans'];
    final usd = data['rates']['usd']['priceTomans'];
    print('18k Gold: $gold18 Toman | USD: $usd Toman');
  }
}
```

---

## ⚙️ How It Works

```
                                ┌─────────────────────────┐
                                │   GitHub Actions Cron   │ (Every 15m)
                                └────────────┬────────────┘
                                             │
               ┌─────────────────────────────┼────────────────────────────┐
               ▼                             ▼                            ▼
      ┌─────────────────┐           ┌─────────────────┐          ┌─────────────────┐
      │    TGJU Feed    │           │   Wallex API    │          │   Nobitex API   │
      │  31 Indicators  │           │   180+ Pairs    │          │  Stats Backup   │
      └────────┬────────┘           └────────┬────────┘          └────────┬────────┘
               │                             │                            │
               └──────────────────────┬──────┴────────────────────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │   Parsian Valuation Math  │
                        └─────────────┬─────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │     Plausibility Gate     │
                        └─────────────┬─────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │       data/*.json         │
                        └───────────────────────────┘
```

1. Aggregates data directly from domestic APIs without web scraping fragility.
2. Mathematically calculates Parsian coin valuations from spot 18k gold.
3. Passes all figures through the anomaly validation gate.
4. Generates granular JSON outputs and commits them cleanly to the repository.

---

## 📄 License

MIT License — Copyright (c) 2026 [Suffergod](https://github.com/Suffergod).
Feel free to use in your own personal finance and tracking applications.
