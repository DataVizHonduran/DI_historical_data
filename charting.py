#!/usr/bin/env python3
"""
analyze_di1_futures.py - Advanced analysis and visualization of DI1 futures

This script extends the basic plotting functionality to include:
1. Yield curve visualization at different points in time
2. Historical volatility calculation
3. Spread analysis between different maturities
4. Interactive plot options using plotly
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import argparse
from datetime import datetime, timedelta

def connect_to_db(db_path):
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        exit(1)

def fetch_di1_data(conn):
    """Fetch all DI1 contracts from the database with comprehensive data."""
    query = """
    SELECT 
        Commodity, 
        Contract_Month, 
        Previous_Price,
        Current_Price,
        Variation,
        Settlement_Value,
        download_date,
        download_time
    FROM all_futures 
    WHERE Commodity LIKE '%DI1%'
    ORDER BY download_date ASC, download_time ASC
    """
    
    try:
        df = pd.read_sql(query, conn)
        # Convert download_date to datetime
        df['download_date'] = pd.to_datetime(df['download_date'])
        
        # Extract maturity information from Contract_Month
        # Assuming format like "J27" for January 2027
        def parse_contract_month(code):
            month_codes = {
                'F': 1,  # January
                'G': 2,  # February
                'H': 3,  # March
                'J': 4,  # April
                'K': 5,  # May
                'M': 6,  # June
                'N': 7,  # July
                'Q': 8,  # August
                'U': 9,  # September
                'V': 10, # October
                'X': 11, # November
                'Z': 12  # December
            }
            
            if len(code) < 2:
                return None, None
                
            month_code = code[0]
            year_code = code[1:]
            
            month = month_codes.get(month_code, None)
            
            try:
                # Assuming '27' means 2027
                if len(year_code) == 2:
                    year = 2000 + int(year_code)
                else:
                    year = int(year_code)
            except ValueError:
                year = None
                
            return month, year
        
        # Apply the parsing function
        df['month'], df['year'] = zip(*df['Contract_Month'].apply(parse_contract_month))
        
        # Create a full maturity date (approximate to 15th of month)
        valid_dates = (df['month'].notna()) & (df['year'].notna())
        df.loc[valid_dates, 'maturity_date'] = df.loc[valid_dates].apply(
            lambda row: pd.Timestamp(int(row['year']), int(row['month']), 15), axis=1
        )
        
        # Calculate days to maturity
        df['days_to_maturity'] = (df['maturity_date'] - df['download_date']).dt.days
        
        # Create a unique contract identifier
        df['contract'] = df['Commodity'] + ' ' + df['Contract_Month']
        
        return df
    except pd.io.sql.DatabaseError as e:
        print(f"Query execution error: {e}")
        exit(1)

def plot_price_evolution(df, output_dir=None):
    """Plot the price evolution of each DI1 contract."""
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    contracts = df['contract'].unique()
    
    plt.figure(figsize=(12, 8))
    
    for contract in contracts:
        contract_data = df[df['contract'] == contract]
        plt.plot(contract_data['download_date'], contract_data['Current_Price'], 
                label=contract)
    
    plt.title('DI1 Futures Prices Over Time')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gcf().autofmt_xdate()
    
    if len(contracts) > 10:
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        plt.legend()
    
    plt.tight_layout()
    
    if output_dir:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(output_dir, f'di1_prices_{timestamp}.png')
        plt.savefig(file_path, dpi=300)
        print(f"Price evolution plot saved to: {file_path}")
    else:
        plt.show()

def calculate_historical_volatility(df, window=30):
    """
    Calculate historical volatility for each contract using a rolling window.
    
    Args:
        df: DataFrame with DI1 contracts data
        window: Number of days for the rolling window (default: 30)
    
    Returns:
        DataFrame with added volatility columns
    """
    result_df = df.copy()
    
    # Group by contract
    for contract in df['contract'].unique():
        contract_data = df[df['contract'] == contract].copy()
        
        # Sort by date
        contract_data = contract_data.sort_values('download_date')
        
        # Calculate daily returns
        contract_data['daily_return'] = contract_data['Current_Price'].pct_change()
        
        # Calculate rolling standard deviation of returns (volatility)
        contract_data['volatility_30d'] = contract_data['daily_return'].rolling(window=window).std() * np.sqrt(252)  # Annualize
        
        # Update the result dataframe
        result_df.loc[contract_data.index, 'volatility_30d'] = contract_data['volatility_30d']
    
    return result_df

def plot_yield_curve(df, output_dir=None):
    """
    Plot the yield curve at different points in time.
    
    Args:
        df: DataFrame with DI1 contracts data
        output_dir: Directory to save plots
    """
    # Get unique dates
    dates = df['download_date'].dt.date.unique()
    
    # Select a few representative dates for clarity
    if len(dates) > 5:
        date_indices = np.linspace(0, len(dates)-1, 5, dtype=int)
        selected_dates = [dates[i] for i in date_indices]
    else:
        selected_dates = dates
    
    plt.figure(figsize=(12, 8))
    
    for date in selected_dates:
        # Filter data for this date
        date_data = df[df['download_date'].dt.date == date]
        
        # Group by maturity and get the latest price for each contract
        latest_data = date_data.sort_values('download_time').groupby('contract').last()
        
        # Sort by days to maturity
        sorted_data = latest_data.sort_values('days_to_maturity')
        
        # Plot the yield curve
        plt.plot(sorted_data['days_to_maturity'], sorted_data['Current_Price'], 
                marker='o', linestyle='-', label=str(date))
    
    plt.title('DI1 Yield Curves Over Time')
    plt.xlabel('Days to Maturity')
    plt.ylabel('Price')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title='Date')
    
    plt.tight_layout()
    
    if output_dir:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(output_dir, f'di1_yield_curve_{timestamp}.png')
        plt.savefig(file_path, dpi=300)
        print(f"Yield curve plot saved to: {file_path}")
    else:
        plt.show()

def plot_volatility(df, output_dir=None):
    """
    Plot historical volatility for each contract.
    
    Args:
        df: DataFrame with DI1 contracts data and volatility
        output_dir: Directory to save plots
    """
    # Get top contracts by trading activity (using frequency in the dataset as a proxy)
    contract_counts = df['contract'].value_counts()
    top_contracts = contract_counts.head(5).index.tolist()
    
    plt.figure(figsize=(12, 8))
    
    for contract in top_contracts:
        contract_data = df[df['contract'] == contract].sort_values('download_date')
        
        # Plot only if we have volatility data
        if 'volatility_30d' in contract_data.columns and contract_data['volatility_30d'].notna().any():
            plt.plot(contract_data['download_date'], contract_data['volatility_30d'], 
                    label=contract)
    
    plt.title('30-Day Historical Volatility of DI1 Contracts')
    plt.xlabel('Date')
    plt.ylabel('Annualized Volatility')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    
    if output_dir:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(output_dir, f'di1_volatility_{timestamp}.png')
        plt.savefig(file_path, dpi=300)
        print(f"Volatility plot saved to: {file_path}")
    else:
        plt.show()

def create_interactive_plot(df, output_dir=None):
    """
    Create an interactive plot using plotly.
    
    Args:
        df: DataFrame with DI1 contracts data
        output_dir: Directory to save HTML file
    """
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Get top contracts by most recent data point
    latest_date = df['download_date'].max()
    latest_data = df[df['download_date'] == latest_date]
    
    top_contracts = latest_data.sort_values('Current_Price', ascending=False).head(5)['contract'].unique()
    
    # Add traces for each contract
    for contract in top_contracts:
        contract_data = df[df['contract'] == contract].sort_values('download_date')
        
        fig.add_trace(
            go.Scatter(
                x=contract_data['download_date'], 
                y=contract_data['Current_Price'],
                name=contract,
                mode='lines',
                hovertemplate='Date: %{x}<br>Price: %{y:.2f}<extra></extra>'
            )
        )
    
    # Add yield curve for the most recent date
    if 'days_to_maturity' in df.columns:
        recent_data = df[df['download_date'] == latest_date].copy()
        recent_data = recent_data.sort_values('days_to_maturity')
        
        fig.add_trace(
            go.Scatter(
                x=recent_data['days_to_maturity'],
                y=recent_data['Current_Price'],
                name='Current Yield Curve',
                mode='markers+lines',
                marker=dict(size=10),
                line=dict(dash='dash'),
                visible='legendonly',
                hovertemplate='Days to Maturity: %{x}<br>Price: %{y:.2f}<extra></extra>'
            ),
            secondary_y=False
        )
    
    # Update layout
    fig.update_layout(
        title='Interactive DI1 Futures Analysis',
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template='plotly_white'
    )
    
    # Add range slider
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )
    
    if output_dir:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(output_dir, f'di1_interactive_{timestamp}.html')
        fig.write_html(file_path)
        print(f"Interactive plot saved to: {file_path}")
        
        # Also save a static image version
        img_path = os.path.join(output_dir, f'di1_interactive_{timestamp}.png')
        fig.write_image(img_path, width=1200, height=800)
        print(f"Static image of interactive plot saved to: {img_path}")
    else:
        # Return the figure to display in a notebook or elsewhere
        return fig

def main():
    """Main function to execute the script."""
    parser = argparse.ArgumentParser(description='Analyze DI1 futures data with advanced visualizations')
    parser.add_argument('--db', type=str, default='b3_futures.db',
                        help='Path to the SQLite database (default: b3_futures.db)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory for saved plots (default: None, just display)')
    parser.add_argument('--interactive', action='store_true',
                        help='Create interactive Plotly visualizations')
    parser.add_argument('--basic', action='store_true',
                        help='Only create basic price evolution plot')
    
    args = parser.parse_args()
    
    # Connect to the database
    conn = connect_to_db(args.db)
    
    # Fetch DI1 data
    print("Fetching DI1 futures data...")
    df = fetch_di1_data(conn)
    
    # Close the connection
    conn.close()
    
    if df.empty:
        print("No DI1 futures data found in the database.")
        return
        
    # Print summary statistics
    print(f"Found {len(df['contract'].unique())} unique DI1 contracts")
    print(f"Date range: {df['download_date'].min().date()} to {df['download_date'].max().date()}")
    
    # Create output directory if needed
    if args.output and not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Plot the data
    print("Creating visualizations...")
    
    # Basic plot
    plot_price_evolution(df, args.output)
    
    if not args.basic:
        # Calculate volatility
        print("Calculating historical volatility...")
        df_with_vol = calculate_historical_volatility(df)
        
        # Create additional plots
        print("Generating yield curve plot...")
        plot_yield_curve(df, args.output)
        
        print("Generating volatility plot...")
        plot_volatility(df_with_vol, args.output)
    
    if args.interactive:
        try:
            import plotly
            print("Creating interactive visualization...")
            fig = create_interactive_plot(df, args.output)
            
            # If not saving, show the plot
            if not args.output and fig:
                fig.show()
                
        except ImportError:
            print("Warning: Plotly is required for interactive visualizations.")
            print("Install with: pip install plotly kaleido")
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()
