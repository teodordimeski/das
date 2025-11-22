#!/usr/bin/env python3
"""
Clean Binance crypto pairs CSV

- Исклучува невалидни, нисколиквидни и нестабилни парови
- Сите други податоци остануваат непроменети
- Работи автоматски, без рачна интервенција
- Чува чист CSV: binance_data_filtered_full.csv
"""

import pandas as pd
import os

INPUT_CSV = "binance_data_top1000.csv"
OUTPUT_CSV = "binance_data_filter1_output.csv"

# Праг за минимален дневен обем (QuoteVolume_24h)
MIN_QUOTE_VOLUME = 10000  # пример: 10,000 USD

# Листа на стабилни quote валути
STABLE_QUOTES = {"USDT", "BUSD", "USDC", "USD", "BTC", "ETH"}

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Не постои CSV фајл: {INPUT_CSV}")
        return

    df = pd.read_csv(INPUT_CSV)

    # 1️⃣ Исклучи делистирани / невалидни (симбол со 0 или None за LastPrice_24h)
    valid_df = df[df["LastPrice_24h"].notna() & (df["LastPrice_24h"] > 0)]

    # 2️⃣ Исклучи нисколиквидни парови
    valid_df = valid_df[valid_df["QuoteVolume_24h"] >= MIN_QUOTE_VOLUME]

    # 3️⃣ Исклучи парови со нестабилни quote валути
    valid_df = valid_df[valid_df["QuoteAsset"].isin(STABLE_QUOTES)]

    # 4️⃣ Зачувај чист CSV
    valid_df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Завршено! Чистиот CSV е зачуван: {OUTPUT_CSV}")
    print(f"📌 Вкупно валидни парови: {len(valid_df)}")

if __name__ == "__main__":
    main()
