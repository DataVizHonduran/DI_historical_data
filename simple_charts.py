import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Connect and get data
conn = sqlite3.connect('b3_futures.db')

# Get unique commodities
commodities = pd.read_sql("SELECT DISTINCT Commodity FROM all_futures", conn)['Commodity'].tolist()

print(f"Creating charts for {len(commodities)} futures contracts...")

# Create chart for each commodity
for i, commodity in enumerate(commodities):
    # Get data
    df = pd.read_sql(f"""
        SELECT * FROM all_futures 
        WHERE Commodity = '{commodity}' 
        ORDER BY download_date
    """, conn)
    
    if len(df) < 2:
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
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save chart
    safe_name = commodity.replace('/', '_').replace(' ', '_')[:30]
    plt.savefig(f'{safe_name}_chart.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ {i+1}/{len(commodities)}: {commodity}")

conn.close()
print("All charts created!")
