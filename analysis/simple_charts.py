#!/usr/bin/env python3
from pathlib import Path
from futures_data_analyzer import FuturesDataAnalyzer

# Always point to the real database and local charts folder
DB_PATH = str(Path(__file__).resolve().parents[1] / "b3_futures.db")
OUT_DIR = Path(__file__).resolve().parents[1] / "charts"
OUT_DIR.mkdir(exist_ok=True)

print("USING DB:", DB_PATH)

analyzer = FuturesDataAnalyzer(DB_PATH)
analyzer.connect_database()

futures_df = analyzer.query_data("SELECT DISTINCT Commodity FROM all_futures")
futures_list = futures_df['Commodity'].tolist()
print(f"Creating charts for {len(futures_list)} futures...")

for commodity in futures_list:
    data = analyzer.get_commodity_history(commodity, days=30)
    if not data.empty:
        chart = analyzer.create_price_trend_chart(data, commodity)
        safe_name = commodity.replace(" ", "_").replace("/", "_")[:30]
        analyzer.save_chart(chart, str(OUT_DIR / f"{safe_name}.html"))
        print(f"✅ {commodity}")

analyzer.disconnect_database()
print("Done!")
