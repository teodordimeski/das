#!/usr/bin/env python3
"""
Clean Binance crypto pairs CSV

- Исклучува невалидни, нисколиквидни и нестабилни парови
- Во излезниот CSV се запишуваат САМО симболите (без дупликати)
"""

import pandas as pd
import os

INPUT_CSV = "binance_data_top1000.csv"
OUTPUT_CSV = "binance_data_filter1_output.csv"

MIN_QUOTE_VOLUME = 10000
STABLE_QUOTES = {"USDT", "BUSD", "USDC", "USD", "BTC", "ETH"}

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Не постои CSV фајл: {INPUT_CSV}")
        return

    df = pd.read_csv(INPUT_CSV)

    # Проверка дали колоните постојат
    required_cols = ["symbol", "LastPrice_24h", "QuoteVolume_24h", "QuoteAsset"]
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ Не постои колоната '{col}' во CSV")
            return

    # Филтрирање на валидни редови
    valid_df = df[df["LastPrice_24h"].notna() & (df["LastPrice_24h"] > 0)]
    valid_df = valid_df[valid_df["QuoteVolume_24h"] >= MIN_QUOTE_VOLUME]
    valid_df = valid_df[valid_df["QuoteAsset"].isin(STABLE_QUOTES)]

    # Само симболи + отстранување дупликати
    symbols_only = valid_df[["symbol"]].drop_duplicates()

    symbols_only.to_csv(OUTPUT_CSV, index=False)

    print(f"✅ Завршено! CSV со само симболи е зачуван: {OUTPUT_CSV}")
    print(f"🔢 Вкупно валидни уникатни симболи: {len(symbols_only)}")

if __name__ == "__main__":
    main()
