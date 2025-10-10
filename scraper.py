import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import sqlite3

def download_b3_futures():
    url = "https://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-ajustes-do-pregao-enUS.asp"
    
    response = requests.get(url)
    response.encoding = 'utf-8'
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table')
    
    data = []
    current_commodity = None
    
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        
        if len(cells) == 6:
            commodity = cells[0].get_text(strip=True)
            contract_month = cells[1].get_text(strip=True)
            previous_price = cells[2].get_text(strip=True)
            current_price = cells[3].get_text(strip=True)
            variation = cells[4].get_text(strip=True)
            settlement_value = cells[5].get_text(strip=True)
            
            if commodity:
                current_commodity = commodity
            
            data.append({
                'Commodity': current_commodity,
                'Contract_Month': contract_month,
                'Previous_Price': previous_price,
                'Current_Price': current_price,
                'Variation': variation,
                'Settlement_Value': settlement_value
            })
    
    df = pd.DataFrame(data)
    
    df['download_date'] = datetime.now().strftime('%Y-%m-%d')
    df['download_time'] = datetime.now().strftime('%H:%M:%S')
    
    return df

def save_to_sqlite(df, db_path='b3_futures.db'):
    conn = sqlite3.connect(db_path)
    
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS all_futures")
    conn.commit()
    
    df.to_sql('all_futures', conn, if_exists='replace', index=False)
    
    conn.commit()
    conn.close()
    
    print(f"Saved {len(df)} records to {db_path}")

if __name__ == "__main__":
    df = download_b3_futures()
    save_to_sqlite(df)
    print(f"\nTotal records: {len(df)}")
    print(f"\nDI1 contracts:")
    print(df[df['Commodity'].str.contains('DI1', na=False)])
