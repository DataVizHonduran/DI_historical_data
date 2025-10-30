#!/usr/bin/env python3
"""
GitHub Actions version of analyze_di1_futures.py

A simplified script to automatically generate DI1 futures charts
from the B3 database. This script is designed to be run as part of
a GitHub Actions workflow.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = 'b3_futures.db'  # Database in repository root
OUTPUT_DIR = './charts'    # Output directory for charts

def connect_to_db():
    """Connect to the SQLite database."""
    try:
        logger.info(f"Connecting to database: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def fetch_di1_data(conn):
    """Fetch all DI1 contracts from the database."""
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
    
    try:
        logger.info("Fetching DI1 futures data...")
        df = pd.read_sql(query, conn)
        
        # Convert download_date to datetime
        df['download_date'] = pd.to_datetime(df['download_date'])
        
        # Create a unique contract identifier
        df['contract'] = df['Commodity'] + ' ' + df['Contract_Month']
        
        logger.info(f"Found {len(df['contract'].unique())} unique DI1 contracts")
        logger.info(f"Date range: {df['download_date'].min().date()} to {df['download_date'].max().date()}")
        
        return df
    except pd.io.sql.DatabaseError as e:
        logger.error(f"Query execution error: {e}")
        raise

def create_charts(df, output_dir):
    """Create and save charts for DI1 contracts."""
    if df.empty:
        logger.warning("No DI1 data to plot.")
        return
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d')
    
    # Create combined chart of all contracts
    logger.info("Creating combined price chart...")
    plt.figure(figsize=(12, 8))
    
    # Get unique contracts
    contracts = df['contract'].unique()
    
    # Plot each contract
    for contract in contracts:
        contract_data = df[df['contract'] == contract]
        plt.plot(contract_data['download_date'], contract_data['Current_Price'], 
                label=contract)
    
    # Format the plot
    plt.title('DI1 Futures Prices Over Time')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Format x-axis to show dates better
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gcf().autofmt_xdate()
    
    # Add legend outside of plot if there are many contracts
    if len(contracts) > 10:
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        plt.legend()
    
    plt.tight_layout()
    
    # Save the combined plot
    file_path = os.path.join(output_dir, f'di1_all_contracts_{timestamp}.png')
    plt.savefig(file_path, dpi=300)
    logger.info(f"Combined chart saved to: {file_path}")
    plt.close()
    
    # Create individual charts for the most recent contracts
    # Get the latest date
    latest_date = df['download_date'].max()
    
    # Get contracts active on the latest date
    recent_contracts = df[df['download_date'] == latest_date]['contract'].unique()
    
    logger.info(f"Creating individual charts for {len(recent_contracts)} active contracts...")
    
    for contract in recent_contracts:
        plt.figure(figsize=(10, 6))
        contract_data = df[df['contract'] == contract]
        
        plt.plot(contract_data['download_date'], contract_data['Current_Price'], 
                marker='o', linestyle='-')
        
        plt.title(f'Price Evolution: {contract}')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gcf().autofmt_xdate()
        
        # Save to a filename that's safe for all filesystems
        safe_contract_name = contract.replace(' ', '_').replace('/', '_')
        file_path = os.path.join(output_dir, f'{safe_contract_name}_{timestamp}.png')
        plt.savefig(file_path, dpi=300)
        plt.close()
    
    # Create an index.html file to easily view all charts
    create_index_html(output_dir, timestamp)
    
    logger.info(f"All charts generated and saved to {output_dir}")

def create_index_html(output_dir, timestamp):
    """Create an HTML index file to view all generated charts."""
    logger.info("Creating index.html...")
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DI1 Futures Charts</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .chart-container { margin-bottom: 30px; }
        img { max-width: 100%; border: 1px solid #ddd; }
        .last-updated { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>DI1 Futures Charts</h1>
    <p class="last-updated">Last updated: {date}</p>
    
    <div class="chart-container">
        <h2>All DI1 Contracts</h2>
        <img src="di1_all_contracts_{timestamp}.png" alt="All DI1 Contracts">
    </div>
    
    <h2>Individual Contract Charts</h2>
""".format(date=datetime.now().strftime('%Y-%m-%d'), timestamp=timestamp)
    
    # Find all individual contract charts
    individual_charts = [f for f in os.listdir(output_dir) 
                        if f.endswith(f'{timestamp}.png') 
                        and not f.startswith('di1_all_contracts')]
    
    # Add each chart to the HTML
    for chart in sorted(individual_charts):
        contract_name = chart.replace('_', ' ').replace(f'_{timestamp}.png', '')
        html_content += f"""
    <div class="chart-container">
        <h3>{contract_name}</h3>
        <img src="{chart}" alt="{contract_name}">
    </div>
"""
    
    # Close the HTML
    html_content += """
</body>
</html>
"""
    
    # Save the HTML file
    with open(os.path.join(output_dir, 'index.html'), 'w') as f:
        f.write(html_content)
    
    logger.info(f"Created index.html in {output_dir}")

def main():
    """Main function to execute the script."""
    try:
        # Connect to database
        conn = connect_to_db()
        
        # Fetch DI1 data
        df = fetch_di1_data(conn)
        
        # Close the connection
        conn.close()
        
        if df.empty:
            logger.warning("No DI1 futures data found. Exiting.")
            return
        
        # Create charts
        create_charts(df, OUTPUT_DIR)
        
        logger.info("Chart generation complete!")
        
    except Exception as e:
        logger.error(f"Error during chart generation: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
