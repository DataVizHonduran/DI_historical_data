import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

# Make sure charts folder exists
os.makedirs('charts', exist_ok=True)
print("Charts folder created")

# Connect to database
conn = sqlite3.connect('b3_futures.db')

# Get all DI1 data
print("Fetching DI1 data...")
df = pd.read_sql("""
    SELECT * FROM all_futures 
    WHERE Commodity LIKE '%DI1%'
    ORDER BY download_date
""", conn)

if df.empty:
    print("No DI1 data found!")
    exit(1)

print(f"Found {len(df)} DI1 data rows")

# Convert date
df['download_date'] = pd.to_datetime(df['download_date'])

# Create a unique ID for each contract
df['contract'] = df['Commodity'] + ' ' + df['Contract_Month']

# Get unique contracts
contracts = df['contract'].unique()
print(f"Found {len(contracts)} unique contracts")

# Create a chart for each contract
for i, contract in enumerate(contracts, 1):
    print(f"Creating chart {i}/{len(contracts)}: {contract}")
    
    # Get data for this contract
    contract_df = df[df['contract'] == contract]
    
    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(contract_df['download_date'], contract_df['Current_Price'], marker='o')
    
    plt.title(contract)
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True)
    plt.tight_layout()
    
    # Save the chart
    filename = contract.replace(' ', '_').replace('/', '_')[:30] + '.png'
    filepath = os.path.join('charts', filename)
    plt.savefig(filepath)
    plt.close()
    
    print(f"Saved to {filepath}")

# Close connection
conn.close()
print("Done!")
