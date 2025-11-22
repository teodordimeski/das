#!/usr/bin/env python3
"""
Extract latest available data for each symbol
and print symbols with outdated data, also save missing symbols to missing.csv
"""

import pandas as pd
import os
from datetime import datetime, timedelta

CSV_INPUT = "binance_data_filter1_output.csv"
CSV_OUTPUT = "binance_data_filter2_output.csv"
MISSING_OUTPUT = "missing.csv"


def main():
    if not os.path.exists(CSV_INPUT):
        print(f"❌ Не постои CSV фајл: {CSV_INPUT}")
        return

    # Чита CSV
    df = pd.read_csv(CSV_INPUT, parse_dates=["date"])

    # Наоѓа последен ред за секој симбол
    latest_rows = df.sort_values("date").groupby("symbol", as_index=False).last()

    # Денес и вчера
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    # Симболи со застарени податоци
    outdated_symbols = latest_rows[~latest_rows["date"].isin([today, yesterday])]["symbol"].tolist()

    if outdated_symbols:
        print("⚠️ Симболи со застарени податоци (немаат info за денес/вчера):")
        for sym in outdated_symbols:
            print(f"  - {sym}")

        # Зачувај missing symbols во CSV
        pd.DataFrame({"symbol": outdated_symbols}).to_csv(MISSING_OUTPUT, index=False)
        print(f"\n✅ Симболи без актуелни податоци се зачувани во {MISSING_OUTPUT}")
    else:
        print("✅ Сите симболи имаат актуелни податоци (денес или вчера)")
        # Дури и ако нема, креирај празен missing.csv
        pd.DataFrame(columns=["symbol"]).to_csv(MISSING_OUTPUT, index=False)

    # Зачувај во нов CSV со последните редови
    latest_rows.to_csv(CSV_OUTPUT, index=False)
    print(f"\n✅ Завршено! Резултатот е зачуван во {CSV_OUTPUT}")
    print(f"📌 Вкупно символи: {len(latest_rows)}")


if __name__ == "__main__":
    main()
