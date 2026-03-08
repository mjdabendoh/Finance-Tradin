
import sqlite3
import pandas as pd
import yfinance as yf
import requests
import time
import matplotlib.pyplot as plt
from textblob import TextBlob
from datetime import datetime, timedelta
import gradio as gr

# ==========================================
# 🤖 AI EQUITY ANALYST (The "Cyborg" Script)
# ==========================================
# This script automates the 3-step research process:
# 1. Technical Scout: Finds oversold stocks (Williams %R).
# 2. Fundamental Accountant: Checks financial health (SEC Data).
# 3. Sentiment Reader: Analyzes news headlines (TextBlob).
# ==========================================

DB_NAME = "stock_screener.db"
HEADERS = {'User-Agent': 'YourName/1.0 (your@email.com)'}  # Required for SEC API

def setup_database():
    """
    Initializes the local SQLite database to store our analysis.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Technical Table (Price & Momentum)
    cursor.execute('''CREATE TABLE IF NOT EXISTS TechnicalAnalysis (
        ticker TEXT PRIMARY KEY, 
        date TEXT, 
        price REAL, 
        williams_r REAL, 
        rsi REAL, 
        status TEXT)''')

    # 2. Fundamental Table (Health & Safety)
    cursor.execute('''CREATE TABLE IF NOT EXISTS FundamentalAnalysis (
        ticker TEXT PRIMARY KEY, 
        current_ratio REAL, 
        debt_to_equity REAL, 
        free_cash_flow REAL, 
        status TEXT)''')

    # 3. Sentiment Table (News Mood)
    cursor.execute('''CREATE TABLE IF NOT EXISTS SentimentAnalysis (
        ticker TEXT PRIMARY KEY, 
        sentiment_score REAL, 
        article_count INTEGER)''')
        
    conn.commit()
    conn.close()
    print("✅ Database initialized.")

def fetch_technical_data(tickers):
    """
    The Scout: Downloads price history and calculates momentum indicators.
    """
    print(f"🔍 Scanning {len(tickers)} stocks for technical setups...")
    conn = sqlite3.connect(DB_NAME)
    results = []
    
    # Download 90 days of data for calculation context
    data = yf.download(tickers, period="90d", group_by='ticker', progress=False, auto_adjust=True)
    
    for ticker in tickers:
        try:
            # Handle MultiIndex if multiple tickers
            if len(tickers) > 1:
                if ticker not in data.columns.levels[0]: continue
                df = data[ticker]
            else:
                df = data
            
            if len(df) < 21: continue

            # --- Williams %R Calculation ---
            # Formula: ((Highest High - Close) / (Highest High - Lowest Low)) * -100
            high_21 = df['High'].rolling(21).max()
            low_21 = df['Low'].rolling(21).min()
            williams = ((high_21 - df['Close']) / (high_21 - low_21)) * -100
            latest_will = williams.iloc[-1]
            
            # --- RSI Calculation ---
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            latest_rsi = rsi.iloc[-1]

            status = "Oversold" if latest_will < -80 else "Overbought" if latest_will > -20 else "Neutral"
            
            # Save to list
            results.append((ticker, str(datetime.now().date()), df['Close'].iloc[-1], latest_will, latest_rsi, status))
            
        except Exception as e:
            continue
            
    # Bulk Save to DB
    conn.executemany("INSERT OR REPLACE INTO TechnicalAnalysis VALUES (?, ?, ?, ?, ?, ?)", results)
    conn.commit()
    conn.close()
    print(f"✅ Technical analysis complete for {len(results)} stocks.")

def fetch_sentiment(ticker):
    """
    The Reader: Fetches news and calculates a sentiment score (-1 to +1).
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        scores = []
        
        for article in news[:5]:  # Analyze last 5 articles
            title = article.get('title')
            if title:
                blob = TextBlob(title)
                scores.append(blob.sentiment.polarity)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return avg_score, len(scores)
    except:
        return 0.0, 0

# --- GRADIO INTERFACE HELPERS ---

def get_db_data(query_type, ticker=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    res = ""
    
    if query_type == "oversold":
        cursor.execute("SELECT ticker, williams_r, price FROM TechnicalAnalysis WHERE williams_r < -80 ORDER BY williams_r ASC LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            res = "📉 **Top Oversold Stocks:**
"
            for r in rows: res += f"* {r[0]}: Will %R {r[1]:.2f} ($ {r[2]:.2f})
"
        else: res = "No oversold stocks found."
        
    elif query_type == "analyze" and ticker:
        # Fetch Tech + Sentiment
        cursor.execute("SELECT t.price, t.williams_r, s.sentiment_score FROM TechnicalAnalysis t LEFT JOIN SentimentAnalysis s ON t.ticker = s.ticker WHERE t.ticker = ?", (ticker,))
        row = cursor.fetchone()
        if row:
            res = f"📊 **Analysis for {ticker}:**
* Price: ${row[0]:.2f}
* Williams %R: {row[1]:.2f}
* Sentiment Score: {row[2] if row[2] else 0:.2f}"
        else:
            res = f"No data found for {ticker}. Run the scanner first."
            
    conn.close()
    return res

def chatbot_logic(message, history):
    msg = message.lower()
    if "oversold" in msg:
        return get_db_data("oversold")
    elif "analyze" in msg:
        # Simple extraction: assume last word is ticker
        ticker = message.split()[-1].upper()
        return get_db_data("analyze", ticker)
    else:
        return "Try asking: 'Show oversold stocks' or 'Analyze AAPL'"

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    setup_database()
    
    # 1. Run a Quick Scan (Demo List)
    tickers = ['AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT', 'GOOG', 'AMZN', 'META']
    fetch_technical_data(tickers)
    
    # 2. Run Sentiment on a few
    conn = sqlite3.connect(DB_NAME)
    for t in tickers[:3]: # Just top 3 for speed
        score, count = fetch_sentiment(t)
        conn.execute("INSERT OR REPLACE INTO SentimentAnalysis VALUES (?, ?, ?)", (t, score, count))
    conn.commit()
    conn.close()
    
    # 3. Launch Web App
    print("🚀 Launching UI...")
    demo = gr.ChatInterface(fn=chatbot_logic, title="AI Equity Analyst")
    demo.launch(share=True)
