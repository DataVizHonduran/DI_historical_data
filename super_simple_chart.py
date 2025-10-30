#!/usr/bin/env python3
"""
super_simple_chart.py - The simplest possible chart generator for DI1 futures
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# Make sure output directory exists
os.makedirs('./charts', exist_ok=True)
print("Output directory: ./charts")

try:
    # Connect to the database
    print("Connecting to database: b3_futures.db")
    conn = sqlite3.connect('b3_futures.db')
    
    # Fetch DI1 data
    print("Fetching DI1 futures data...")
    query = """
    SELECT 
        Commodity, 
        Contract_Month, 
        Current_Price, 
        download_date 
    FROM all_futures 
    WHERE Commodity LIKE '%DI1%'
    ORDER BY download_date ASC
    """
    
    df = pd.read_sql(query, conn)
    
    # Close connection
    conn.close()
    
    if df.empty:
        print("No DI1 futures data found in the database.")
        exit(1)
    
    # Convert download_date to datetime
    df['download_date'] = pd.to_datetime(df['download_date'])
    
    # Create a unique contract identifier
    df['contract'] = df['Commodity'] + ' ' + df['Contract_Month']
    
    # Print summary info
    print(f"Found {len(df['contract'].unique())} unique DI1 contracts")
    print(f"Date range: {df['download_date'].min().date()} to {df['download_date'].max().date()}")
    
    # Get top contracts by most recent date
    latest_date = df['download_date'].max()
    top_contracts = df[df['download_date'] == latest_date]['contract'].unique()[:5]
    
    # Create a figure for all contracts
    print("Creating main chart...")
    plt.figure(figsize=(12, 8))
    
    # Plot each top contract
    for contract in top_contracts:
        contract_data = df[df['contract'] == contract]
        plt.plot(contract_data['download_date'], contract_data['Current_Price'], 
                label=contract)
    
    # Format the plot
    plt.title('Top 5 DI1 Futures Contracts')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True)
    plt.legend()
    
    # Save the chart
    output_path = './charts/di1_top_contracts.png'
    plt.savefig(output_path)
    print(f"Chart saved to: {output_path}")
    
    print("SUCCESS: Chart generation complete!")
    
except Exception as e:
    print(f"ERROR: {e}")
