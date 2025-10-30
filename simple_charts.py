import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

# Make sure charts folder exists
os.makedirs('charts', exist_ok=True)
print(f"Creating charts folder: {os.path.abspath('charts')}")

# Connect to database
conn = sqlite3.connect('b3_futures.db')

# Get DI1 data
print("Fetching DI1 futures data...")
di1_data = pd.read_sql("""
    SELECT 
        Commodity, 
        Contract_Month, 
        Current_Price, 
        Previous_Price,
        Variation,
        download_date 
    FROM all_futures 
    WHERE Commodity LIKE '%DI1%'
    ORDER BY download_date
""", conn)

# Convert download_date to datetime
di1_data['download_date'] = pd.to_datetime(di1_data['download_date'])

# Create a unique identifier for each contract
di1_data['contract_id'] = di1_data['Commodity'] + ' ' + di1_data['Contract_Month']

# Get unique contracts
unique_contracts = di1_data['contract_id'].unique()
print(f"Found {len(unique_contracts)} unique DI1 contracts")

# Create separate chart for each contract
for i, contract_id in enumerate(unique_contracts):
    # Filter data for this contract
    contract_data = di1_data[di1_data['contract_id'] == contract_id].sort_values('download_date')
    
    if len(contract_data) < 2:
        print(f"Skipping {contract_id}: Not enough data points")
        continue
    
    # Extract contract details
    commodity = contract_data['Commodity'].iloc[0]
    contract_month = contract_data['Contract_Month'].iloc[0]
    
    # Create chart
    plt.figure(figsize=(10, 6))
    
    # Plot price
    plt.plot(contract_data['download_date'], contract_data['Current_Price'], 
             marker='o', linewidth=2, label='Price')
    
    # Format the chart
    plt.title(f'{commodity} - {contract_month} Contract')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    
    # Add some stats to the chart
    latest_price = contract_data['Current_Price'].iloc[-1]
    first_price = contract_data['Current_Price'].iloc[0]
    change = latest_price - first_price
    pct_change = (change / first_price) * 100 if first_price != 0 else 0
    
    stats_text = (
        f"Latest: {latest_price:.2f}\n"
        f"Change: {change:.2f} ({pct_change:.2f}%)"
    )
    
    # Add stats text to the chart
    plt.annotate(stats_text, xy=(0.02, 0.95), xycoords='axes fraction',
                 bbox=dict(boxstyle='round,pad=0.5', fc='lightyellow', alpha=0.7))
    
    plt.tight_layout()
    
    # Save chart
    safe_name = contract_id.replace('/', '_').replace(' ', '_')[:40]
    file_path = f'charts/{safe_name}_chart.png'
    plt.savefig(file_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ {i+1}/{len(unique_contracts)}: {contract_id}")

# Create an index.html file
print("Creating index.html...")
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>DI1 Futures Contracts</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .charts { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; }
        .chart { border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
        .chart h2 { margin-top: 0; font-size: 16px; }
        img { max-width: 100%; }
        .updated { color: #666; font-style: italic; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>DI1 Futures Contracts Charts</h1>
    <p class="updated">Last updated: """ + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    <div class="charts">
"""

# Add each chart to the HTML
for contract_id in unique_contracts:
    safe_name = contract_id.replace('/', '_').replace(' ', '_')[:40]
    file_name = f'{safe_name}_chart.png'
    
    # Check if the file exists
    if os.path.exists(f'charts/{file_name}'):
        html_content += f"""
        <div class="chart">
            <h2>{contract_id}</h2>
            <img src="{file_name}" alt="{contract_id}" />
        </div>
        """

# Close the HTML
html_content += """
    </div>
</body>
</html>
"""

# Save the HTML file
with open('charts/index.html', 'w') as f:
    f.write(html_content)

# Close connection
conn.close()
print("All DI1 contract charts created and saved to charts/ folder!")
