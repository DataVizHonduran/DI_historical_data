#!/usr/bin/env python3
"""
Futures Data Analyzer
A comprehensive script to pull from Git, query the all_futures database, and create interactive Plotly charts.
"""

import os
import sys
import subprocess
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FuturesDataAnalyzer:
    def __init__(self, db_path, repo_path=None):
        """
        Initialize the Futures Data Analyzer
        
        Args:
            db_path (str): Path to the SQLite database file
            repo_path (str): Path to the Git repository (optional)
        """
        self.db_path = db_path
        self.repo_path = repo_path
        self.conn = None
        
    def git_pull(self):
        """Pull latest changes from Git repository"""
        if not self.repo_path:
            logger.warning("No repository path provided, skipping Git pull")
            return
            
        try:
            logger.info(f"Pulling latest changes from {self.repo_path}")
            result = subprocess.run(
                ['git', 'pull'], 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True, 
                check=True
            )
            logger.info(f"Git pull successful: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Git pull failed: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error("Git not found. Please install Git or check your PATH")
            raise
    
    def connect_database(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect_database(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def query_data(self, query):
        """Execute SQL query and return DataFrame"""
        if not self.conn:
            raise ValueError("Database not connected. Call connect_database() first.")
        
        try:
            df = pd.read_sql_query(query, self.conn)
            logger.info(f"Query executed successfully, returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_all_data(self):
        """Get all data from the all_futures table"""
        query = """
        SELECT * FROM all_futures
        ORDER BY download_date DESC, download_time DESC
        """
        return self.query_data(query)
    
    def get_latest_data(self):
        """Get the most recent data for each commodity"""
        query = """
        SELECT *
        FROM all_futures a1
        WHERE (a1.download_date, a1.download_time) = (
            SELECT MAX(a2.download_date), MAX(a2.download_time)
            FROM all_futures a2
            WHERE a2.Commodity = a1.Commodity 
            AND a2.Contract_Month = a1.Contract_Month
            AND a2.download_date = (SELECT MAX(download_date) FROM all_futures)
        )
        ORDER BY a1.Commodity, a1.Contract_Month
        """
        return self.query_data(query)
    
    def get_commodity_history(self, commodity, days=30):
        """Get historical data for a specific commodity"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = f"""
        SELECT *
        FROM all_futures
        WHERE Commodity = '{commodity}'
        AND download_date >= '{cutoff_date}'
        ORDER BY download_date, download_time
        """
        return self.query_data(query)
    
    def create_price_trend_chart(self, df, commodity=None):
        """Create a price trend chart for commodities"""
        fig = go.Figure()
        
        if commodity:
            # Single commodity chart
            df_filtered = df[df['Commodity'] == commodity]
            df_filtered['datetime'] = pd.to_datetime(df_filtered['download_date'] + ' ' + df_filtered['download_time'])
            
            for contract in df_filtered['Contract_Month'].unique():
                contract_data = df_filtered[df_filtered['Contract_Month'] == contract]
                fig.add_trace(go.Scatter(
                    x=contract_data['datetime'],
                    y=contract_data['Current_Price'],
                    mode='lines+markers',
                    name=f"{commodity} {contract}",
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                'Price: %{y:,.2f} BRL<br>' +
                                'Date: %{x}<br>' +
                                '<extra></extra>'
                ))
            
            fig.update_layout(
                title=f"Price Trends - {commodity}",
                xaxis_title="Date",
                yaxis_title="Price (BRL)",
                hovermode='x unified'
            )
        else:
            # Multiple commodities - show latest prices
            latest_data = self.get_latest_data()
            
            fig = px.bar(
                latest_data,
                x='Commodity',
                y='Current_Price',
                color='Variation',
                hover_data=['Contract_Month', 'Previous_Price', 'Settlement_Value'],
                title="Current Prices by Commodity",
                color_continuous_scale='RdYlGn'
            )
            
            fig.update_layout(
                xaxis_title="Commodity",
                yaxis_title="Current Price (BRL)",
                xaxis={'tickangle': 45}
            )
        
        return fig
    
    def create_variation_heatmap(self, df):
        """Create a heatmap showing daily variations"""
        latest_data = self.get_latest_data()
        
        # Pivot data for heatmap
        pivot_data = latest_data.pivot_table(
            index='Commodity',
            columns='Contract_Month',
            values='Variation',
            fill_value=0
        )
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale='RdYlGn',
            hovertemplate='<b>%{y}</b><br>' +
                         'Contract: %{x}<br>' +
                         'Variation: %{z:,.2f}<br>' +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title="Daily Variation Heatmap",
            xaxis_title="Contract Month",
            yaxis_title="Commodity"
        )
        
        return fig
    
    def create_volume_analysis(self, df):
        """Create volume analysis charts"""
        latest_data = self.get_latest_data()
        
        # Settlement value by commodity
        commodity_totals = latest_data.groupby('Commodity')['Settlement_Value'].sum().reset_index()
        commodity_totals = commodity_totals.sort_values('Settlement_Value', ascending=True)
        
        fig = px.bar(
            commodity_totals,
            x='Settlement_Value',
            y='Commodity',
            orientation='h',
            title="Settlement Values by Commodity (Latest Data)",
            labels={'Settlement_Value': 'Settlement Value (BRL)', 'Commodity': 'Commodity'}
        )
        
        fig.update_layout(
            height=max(400, len(commodity_totals) * 30),
            yaxis={'tickfont': {'size': 10}}
        )
        
        return fig
    
    def create_dashboard(self, commodity=None, days=30):
        """Create a comprehensive dashboard"""
        logger.info("Creating comprehensive dashboard...")
        
        # Get data
        if commodity:
            df = self.get_commodity_history(commodity, days)
            if df.empty:
                logger.warning(f"No data found for commodity: {commodity}")
                return None
        else:
            df = self.get_all_data()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Price Trends", "Daily Variations", "Settlement Values", "Price Distribution"),
            specs=[[{"type": "scatter"}, {"type": "heatmap"}],
                   [{"type": "bar"}, {"type": "histogram"}]]
        )
        
        # 1. Price trends
        latest_data = self.get_latest_data()
        if commodity:
            commodity_data = latest_data[latest_data['Commodity'] == commodity]
        else:
            commodity_data = latest_data.head(10)  # Top 10 for readability
        
        fig.add_trace(
            go.Scatter(
                x=commodity_data['Contract_Month'],
                y=commodity_data['Current_Price'],
                mode='markers',
                name="Current Prices",
                marker=dict(size=8, color=commodity_data['Variation'], colorscale='RdYlGn')
            ),
            row=1, col=1
        )
        
        # 2. Variation heatmap (simplified)
        variation_data = latest_data.groupby('Commodity')['Variation'].mean().reset_index().head(10)
        fig.add_trace(
            go.Bar(
                x=variation_data['Commodity'],
                y=variation_data['Variation'],
                name="Avg Variation",
                marker_color=variation_data['Variation'],
                marker_colorscale='RdYlGn'
            ),
            row=1, col=2
        )
        
        # 3. Settlement values
        settlement_data = latest_data.groupby('Commodity')['Settlement_Value'].sum().reset_index().head(10)
        fig.add_trace(
            go.Bar(
                x=settlement_data['Commodity'],
                y=settlement_data['Settlement_Value'],
                name="Settlement Values"
            ),
            row=2, col=1
        )
        
        # 4. Price distribution
        fig.add_trace(
            go.Histogram(
                x=latest_data['Current_Price'],
                name="Price Distribution",
                nbinsx=20
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            title_text=f"Futures Analysis Dashboard{' - ' + commodity if commodity else ''}",
            showlegend=False
        )
        
        return fig
    
    def save_chart(self, fig, filename):
        """Save chart as HTML file"""
        output_path = f"/mnt/user-data/outputs/{filename}"
        fig.write_html(output_path)
        logger.info(f"Chart saved to {output_path}")
        return output_path
    
    def run_analysis(self, commodity=None, days=30, save_charts=True):
        """Run complete analysis workflow"""
        try:
            # Pull from Git if repo specified
            if self.repo_path:
                self.git_pull()
            
            # Connect to database
            self.connect_database()
            
            # Create charts
            charts = {}
            
            # Price trend chart
            df = self.get_commodity_history(commodity, days) if commodity else self.get_all_data()
            charts['price_trends'] = self.create_price_trend_chart(df, commodity)
            
            # Variation heatmap
            charts['variation_heatmap'] = self.create_variation_heatmap(df)
            
            # Volume analysis
            charts['volume_analysis'] = self.create_volume_analysis(df)
            
            # Dashboard
            charts['dashboard'] = self.create_dashboard(commodity, days)
            
            # Save charts if requested
            if save_charts:
                for chart_name, fig in charts.items():
                    if fig:
                        self.save_chart(fig, f"{chart_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            
            return charts
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
        finally:
            self.disconnect_database()

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Futures Data Analyzer")
    parser.add_argument("--db-path", required=True, help="Path to SQLite database")
    parser.add_argument("--repo-path", help="Path to Git repository")
    parser.add_argument("--commodity", help="Specific commodity to analyze")
    parser.add_argument("--days", type=int, default=30, help="Number of days of history to analyze")
    parser.add_argument("--no-save", action="store_true", help="Don't save charts to files")
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = FuturesDataAnalyzer(args.db_path, args.repo_path)
    
    # Run analysis
    try:
        charts = analyzer.run_analysis(
            commodity=args.commodity,
            days=args.days,
            save_charts=not args.no_save
        )
        
        logger.info("Analysis completed successfully!")
        
        # Show available charts
        for chart_name in charts.keys():
            if charts[chart_name]:
                logger.info(f"Created chart: {chart_name}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
