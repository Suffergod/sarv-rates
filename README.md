# sarv-rates

Market rates data pipeline for [Sarv](https://github.com/Suffergod/Sarv-V2).

Fetches, validates, and writes live gold, coins (including Parsians), world currencies, and crypto prices in Tomans every 15 minutes via GitHub Actions.

## Feeds

- `data/rates.json`: full dataset
- `data/rates_compact.json`: minified payload for mobile
- `data/gold.json`: gold, coins, and Parsian series
- `data/fiat.json`: world currencies
- `data/crypto.json`: cryptocurrencies quoted in Tomans

## Run locally

```bash
python sync.py
```
