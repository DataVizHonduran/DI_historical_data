#!/usr/bin/env python3
"""
Really simple: Generate charts for all futures
"""

from futures_data_analyzer import FuturesDataAnalyzer

# Update this path
DB_PATH = "DI_historical_data.db" 

# Create analyzer and connect
analyzer = FuturesDataAnalyzer(DB_PATH)
analyzer.connect_database()

# Get all futures
futures_df = analyzer.query_data("SELECT DISTINCT Commodity FROM all_futures")
futures_list = futures_df['Commodity'].tolist()

print(f"Creating charts for {len(futures_list)} futures...")

# Make chart for each future
for commodity in futures_list:
    data = analyzer.get_commodity_history(commodity, days=30)
    if not data.empty:
        chart = analyzer.create_price_trend_chart(data, commodity)
        safe_name = commodity.replace(" ", "_").replace("/", "_")[:30]
        analyzer.save_chart(chart, f"{safe_name}.html")
        print(f"✅ {commodity}")

analyzer.disconnect_database()
print("Done!")
