#!/usr/bin/env python3
"""
di1_charts.py - Create charts for DI1 futures contracts and save to the charts folder
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

# Make sure charts folder exists
os.makedirs('charts', exist_ok=True)
print("Saving charts to charts/ directory")

# Connect and get data
conn = sqlite3.connect('b3_futures.db')

# Get only DI1 commodities
commodities = pd.read_sql(
    "SELECT DISTINCT Commodity FROM all_futures WHERE Commodity LIKE '%DI1%'", 
    conn
)['Commodity'].tolist()

print(f"Creating charts for {len(commodities)} DI1 futures contracts...")

# Create chart for each DI1 commodity
for i, commodity in enumerate(commodities):
    # Get data
    df = pd.read_sql(f"""
        SELECT * FROM all_futures 
        WHERE Commodity = '{commodity}' 
        ORDER BY download_date
    """, conn)
    
    if len(df) < 2:
        print(f"Skipping {commodity}: Not enough data points")
        continue
    
    # Convert date
    df['download_date'] = pd.to_datetime(df['download_date'])
    
    # Create simple price chart
    plt.figure(figsize=(10, 6))
    
    # Plot each contract month
    for contract in df['Contract_Month'].unique():
        contract_data = df[df['Contract_Month'] == contract]
        plt.plot(contract_data['download_date'], 
                contract_data['Current_Price'], 
                marker='o', label=contract)
    
    plt.title(f'{commodity} - Price Evolution')
    plt.xlabel('Date')
    plt.ylabel('Price (BRL)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save chart to charts folder
    safe_name = commodity.replace('/', '_').replace(' ', '_')[:30]
    file_path = f'charts/{safe_name}_chart.png'
    plt.savefig(file_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ {i+1}/{len(commodities)}: {commodity} → {file_path}")

# Create an index.html file in the charts folder
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>DI1 Futures Charts</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .chart { margin: 20px 0; border: 1px solid #ddd; padding: 10px; }
        img { max-width: 100%; }
    </style>
</head>
<body>
    <h1>DI1 Futures Charts</h1>
    <p>Last updated: """ + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
"""

# Add each chart to the HTML
for commodity in commodities:
    safe_name = commodity.replace('/', '_').replace(' ', '_')[:30]
    file_name = f'{safe_name}_chart.png'
    html_content += f"""
    <div class="chart">
        <h2>{commodity}</h2>
        <img src="{file_name}" alt="{commodity}" />
    </div>
    """

# Close the HTML
html_content += """
</body>
</html>
"""

# Save the HTML file
with open('charts/index.html', 'w') as f:
    f.write(html_content)

print(f"Created index.html with links to all {len(commodities)} charts")

# Close connection
conn.close()
print("All DI1 charts created and saved to charts/ folder!")
