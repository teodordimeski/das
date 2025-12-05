#!/usr/bin/env python3
import pandas as pd
import os
from datetime import datetime, timedelta

CSV_SYMBOLS = "binance_data_filter1_output.csv"
CSV_TOP = "binance_data_top1000.csv"
CSV_OUTPUT = "binance_data_filter2_output.csv"

DATE_COLUMN = "date"

POSSIBLE_SYMBOL_COLUMNS = ["symbol", "Symbol", "pair", "Pair", "baseAsset"]

def detect_symbol_column(df):
    for col in POSSIBLE_SYMBOL_COLUMNS:
        if col in df.columns:
            return col
    raise Exception("❌ Нема колонa за симболи во CSV!")

def main():
    if not os.path.exists(CSV_SYMBOLS):
        print(f"❌ Не постои CSV фајл: {CSV_SYMBOLS}")
        return
    if not os.path.exists(CSV_TOP):
        print(f"❌ Не постои CSV фајл: {CSV_TOP}")
        return

    symbols_df = pd.read_csv(CSV_SYMBOLS)
    symbols_col = detect_symbol_column(symbols_df)
    symbols = symbols_df[symbols_col].unique()

    top_df = pd.read_csv(CSV_TOP, parse_dates=[DATE_COLUMN])
    top_symbol_col = detect_symbol_column(top_df)

    filtered = top_df[top_df[top_symbol_col].isin(symbols)]
    print("Filtered rows:", len(filtered))

    if filtered.empty:
        print("❌ НЕМА СОВПАЃАЊЕ МЕЃУ СИМБОЛИТЕ!")
        return

    latest_data = (
        filtered.sort_values(DATE_COLUMN)
        .groupby(top_symbol_col, as_index=False)[DATE_COLUMN]
        .last()
    )

    latest_data.to_csv(CSV_OUTPUT, index=False)
    print(f"✅ Креиран CSV: {CSV_OUTPUT}")

if __name__ == "__main__":
    main()
