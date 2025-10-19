# Futures Data Analyzer

A comprehensive Python tool for analyzing futures data, with Git integration and interactive Plotly visualizations.

## Features

- **Git Integration**: Automatically pull latest changes from your repository
- **Database Connectivity**: Direct SQLite database querying with pandas
- **Interactive Charts**: Beautiful Plotly visualizations including:
  - Price trend analysis
  - Variation heatmaps
  - Volume analysis
  - Comprehensive dashboards
- **Flexible Querying**: Custom SQL queries and pre-built analysis functions
- **Command Line Interface**: Easy-to-use CLI for automated analysis

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Alternative manual installation**:
   ```bash
   pip install pandas plotly
   ```

## Database Schema

The script expects a SQLite database with the following `all_futures` table structure:

| Column | Description |
|--------|-------------|
| `Commodity` | Contract name (e.g., "DI1 - 1-day Interbank Deposits") |
| `Contract_Month` | Maturity month (e.g., "J27" = January 2027) |
| `Previous_Price` | Previous settlement price |
| `Current_Price` | Current settlement price |
| `Variation` | Daily change |
| `Settlement_Value` | Settlement value in BRL |
| `download_date` | Date scraped (YYYY-MM-DD) |
| `download_time` | Time scraped (HH:MM:SS) |

## Usage

### Command Line Interface

**Basic usage:**
```bash
python futures_data_analyzer.py --db-path path/to/your/database.db
```

**With Git repository:**
```bash
python futures_data_analyzer.py --db-path path/to/database.db --repo-path path/to/git/repo
```

**Analyze specific commodity:**
```bash
python futures_data_analyzer.py --db-path path/to/database.db --commodity "DI1 - 1-day Interbank Deposits"
```

**Custom time range:**
```bash
python futures_data_analyzer.py --db-path path/to/database.db --days 60
```

**Command line options:**
- `--db-path`: Path to SQLite database (required)
- `--repo-path`: Path to Git repository (optional)
- `--commodity`: Specific commodity to analyze (optional)
- `--days`: Number of days of history to analyze (default: 30)
- `--no-save`: Don't save charts to files

### Python API

```python
from futures_data_analyzer import FuturesDataAnalyzer

# Initialize analyzer
analyzer = FuturesDataAnalyzer(
    db_path="path/to/your/database.db",
    repo_path="path/to/git/repo"  # optional
)

# Connect to database
analyzer.connect_database()

# Get latest data
latest_data = analyzer.get_latest_data()

# Get commodity history
history = analyzer.get_commodity_history("DI1 - 1-day Interbank Deposits", days=30)

# Create charts
price_chart = analyzer.create_price_trend_chart(latest_data)
heatmap = analyzer.create_variation_heatmap(latest_data)
dashboard = analyzer.create_dashboard()

# Save charts
analyzer.save_chart(price_chart, "price_trends.html")

# Custom queries
custom_data = analyzer.query_data("""
    SELECT * FROM all_futures 
    WHERE Variation > 5.0 
    ORDER BY download_date DESC
""")

# Clean up
analyzer.disconnect_database()
```

### Quick Start Example

```python
# See example_usage.py for a complete working example
python example_usage.py
```

## Chart Types

### 1. Price Trend Charts
- Line charts showing price movements over time
- Multiple contract months for single commodities
- Interactive hover information

### 2. Variation Heatmaps
- Visual representation of daily price changes
- Color-coded for easy identification of hot/cold spots
- Organized by commodity and contract month

### 3. Volume Analysis
- Bar charts of settlement values
- Horizontal layout for easy comparison
- Sorted by volume for insights

### 4. Comprehensive Dashboard
- Multi-panel view combining multiple chart types
- Overview of market conditions
- Customizable by commodity and time range

## Git Integration

The tool can automatically pull the latest changes from your Git repository before running analysis:

```bash
# This will run 'git pull' in the specified directory before analysis
python futures_data_analyzer.py --db-path database.db --repo-path /path/to/repo
```

## Database Queries

### Pre-built Queries

1. **Get Latest Data**: Most recent data for each commodity/contract
2. **Get All Data**: Complete historical dataset
3. **Get Commodity History**: Historical data for specific commodity

### Custom Queries

```python
# Example: Find highest variations
query = """
SELECT Commodity, Contract_Month, Variation
FROM all_futures
WHERE download_date = (SELECT MAX(download_date) FROM all_futures)
ORDER BY ABS(Variation) DESC
LIMIT 10
"""

data = analyzer.query_data(query)
```

## Output

- **Charts**: Saved as interactive HTML files in `/mnt/user-data/outputs/`
- **Data**: Returned as pandas DataFrames for further analysis
- **Logs**: Comprehensive logging for troubleshooting

## Error Handling

The script includes comprehensive error handling for:
- Database connection issues
- Git operation failures
- Invalid queries
- Missing data

## Customization

The `FuturesDataAnalyzer` class can be easily extended:

```python
class CustomAnalyzer(FuturesDataAnalyzer):
    def custom_analysis(self):
        # Your custom analysis here
        pass
```

## Requirements

- Python 3.7+
- pandas
- plotly
- SQLite3 (built-in with Python)
- Git (for repository operations)

## Troubleshooting

1. **Database Connection Issues**: Verify the database path and file permissions
2. **Git Errors**: Ensure Git is installed and the repository path is correct
3. **Memory Issues**: For large datasets, consider using date filters or limiting results
4. **Import Errors**: Verify all dependencies are installed: `pip install -r requirements.txt`

## Examples

Check `example_usage.py` for comprehensive usage examples including:
- Basic data retrieval
- Chart creation
- Custom queries
- Error handling
