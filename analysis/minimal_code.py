#!/usr/bin/env python3
"""
Minimal DI Futures Charts Generator
Uses exact schema: all_futures table with known columns
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
import os
from pathlib import Path

def find_database():
    """Find the database file in common locations"""
    possible_paths = [
        'b3_futures.db',           # Current directory
        '../b3_futures.db',        # Parent directory (if in analysis/)
        'DI_historical_data.db',   # Alternative name current
        '../DI_historical_data.db', # Alternative name parent
        'data/b3_futures.db',      # Data subfolder
        '../data/b3_futures.db'    # Data subfolder in parent
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found database: {path}")
            return path
    
    print("❌ Database not found. Looking for files...")
    # Search for any .db files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db'):
                found_path = os.path.join(root, file)
                print(f"   Found: {found_path}")
                return found_path
    
    return None

def create_price_chart(commodity, df, output_dir="."):
    """Create price chart for one commodity"""
    commodity_data = df[df['Commodity'] == commodity].copy()
    
    if commodity_data.empty:
        return None
    
    # Convert date to datetime for proper sorting
    commodity_data['datetime'] = pd.to_datetime(commodity_data['download_date'] + ' ' + commodity_data['download_time'])
    commodity_data = commodity_data.sort_values('datetime')
    
    fig = go.Figure()
    
    # Group by contract month to show different maturity lines
    for contract in commodity_data['Contract_Month'].unique():
        contract_data = commodity_data[commodity_data['Contract_Month'] == contract]
        
        fig.add_trace(go.Scatter(
            x=contract_data['datetime'],
            y=contract_data['Current_Price'],
            mode='lines+markers',
            name=f"{contract}",
            line=dict(width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>{contract}</b><br>" +
                         "Date: %{x}<br>" +
                         "Price: %{y:,.2f} BRL<br>" +
                         "<extra></extra>"
        ))
    
    # Clean up title
    clean_name = commodity.replace(" - ", " ").replace("-", " ")
    
    fig.update_layout(
        title=f"Price History: {clean_name}",
        xaxis_title="Date",
        yaxis_title="Price (BRL)",
        hovermode='x unified',
        showlegend=True,
        width=1000,
        height=600,
        template="plotly_white"
    )
    
    # Create safe filename
    safe_name = commodity.replace(" ", "_").replace("-", "_").replace("/", "_").replace(",", "")
    filename = os.path.join(output_dir, f"{safe_name}.html")
    
    fig.write_html(filename)
    return filename

def main():
    print("🚀 DI Futures Price Charts Generator")
    print("=" * 50)
    
    # Find database
    db_path = find_database()
    if not db_path:
        print("❌ Could not find database file!")
        print("Expected: b3_futures.db or DI_historical_data.db")
        return
    
    # Connect and load data
    try:
        conn = sqlite3.connect(db_path)
        print(f"📊 Loading data from table: all_futures")
        
        # Load all data
        df = pd.read_sql_query("SELECT * FROM all_futures", conn)
        print(f"✅ Loaded {len(df)} records")
        
        # Get unique commodities
        commodities = df['Commodity'].unique()
        print(f"📈 Found {len(commodities)} different futures:")
        
        for i, commodity in enumerate(commodities, 1):
            print(f"   {i:2d}. {commodity}")
        
        print(f"\n🎨 Creating charts...")
        
        # Create output directory if needed
        output_dir = "charts"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate charts
        created_charts = []
        for i, commodity in enumerate(commodities, 1):
            print(f"   {i:2d}/{len(commodities)} {commodity[:50]}...")
            
            chart_file = create_price_chart(commodity, df, output_dir)
            if chart_file:
                created_charts.append(chart_file)
        
        conn.close()
        
        print(f"\n🎉 Success! Created {len(created_charts)} charts")
        print(f"📁 Charts saved in: {os.path.abspath(output_dir)}/")
        
        if created_charts:
            print(f"\n📖 Example: open {created_charts[0]} in your browser")
            
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print(f"❌ Table 'all_futures' not found in database!")
            print("   Run database_inspector.py to see available tables")
        else:
            print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
