import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import time

st.set_page_config(page_title="TSX AI Engine", layout="wide")
st.title("🇨🇦 TSX AI Signal Engine – Level 4")

ACCOUNT_SIZE = 100000
RISK_PERCENT = 1

stocks = [
    "SHOP.TO","SU.TO","RY.TO","TD.TO","BNS.TO",
    "ENB.TO","CNQ.TO","CP.TO","CNR.TO","BAM.TO"
]

def calculate_score(df_daily, df_hourly):

    score = 0

    last_d = df_daily.iloc[-1]
    last_h = df_hourly.iloc[-1]

    # Trend strength (30%)
    if last_d["EMA20"] > last_d["EMA50"]:
        score += 30

    # Momentum (20%)
    if 55 < last_d["RSI"] < 75:
        score += 20

    # Volume surge (15%)
    if last_d["Volume"] > df_daily["Volume"].rolling(20).mean().iloc[-1]:
        score += 15

    # Multi-timeframe confirmation (25%)
    if last_h["EMA20"] > last_h["EMA50"]:
        score += 25

    # Volatility stability (10%)
    if last_d["ATR"] < df_daily["ATR"].rolling(20).mean().iloc[-1]:
        score += 10

    return score

results = []

for ticker in stocks:

    df_daily = yf.download(ticker, period="6mo", interval="1d")
    df_hourly = yf.download(ticker, period="30d", interval="1h")

    if df_daily.empty or df_hourly.empty:
        continue

    if isinstance(df_daily.columns, pd.MultiIndex):
        df_daily.columns = df_daily.columns.get_level_values(0)
    if isinstance(df_hourly.columns, pd.MultiIndex):
        df_hourly.columns = df_hourly.columns.get_level_values(0)

    # Daily indicators
    df_daily["EMA20"] = ta.trend.ema_indicator(df_daily["Close"], 20)
    df_daily["EMA50"] = ta.trend.ema_indicator(df_daily["Close"], 50)
    df_daily["RSI"] = ta.momentum.rsi(df_daily["Close"], 14)
    df_daily["ATR"] = ta.volatility.average_true_range(
        df_daily["High"], df_daily["Low"], df_daily["Close"], 14
    )

    # Hourly indicators
    df_hourly["EMA20"] = ta.trend.ema_indicator(df_hourly["Close"], 20)
    df_hourly["EMA50"] = ta.trend.ema_indicator(df_hourly["Close"], 50)

    score = calculate_score(df_daily, df_hourly)

    entry = float(df_daily["Close"].iloc[-1])
    atr = float(df_daily["ATR"].iloc[-1])

    stop = entry - atr
    target = entry + (2 * atr)

    risk_amount = ACCOUNT_SIZE * (RISK_PERCENT / 100)
    shares = int(risk_amount / (entry - stop)) if (entry - stop) > 0 else 0

    grade = "C"
    if score >= 85:
        grade = "A+"
    elif score >= 75:
        grade = "A"
    elif score >= 60:
        grade = "B"

    results.append({
        "Stock": ticker,
        "Price": round(entry,2),
        "Score": score,
        "Grade": grade,
        "Stop": round(stop,2),
        "Target": round(target,2),
        "Shares (1%)": shares
    })

if len(results) > 0:

    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values(by="Score", ascending=False)

    best = df_results.iloc[0]

    st.subheader("🔥 Best AI Trade")

    col1, col2, col3 = st.columns(3)
    col1.metric("Stock", best["Stock"])
    col2.metric("AI Score", best["Score"])
    col3.metric("Grade", best["Grade"])

    st.write("### Trade Plan")
    st.write(f"Entry: {best['Price']}")
    st.write(f"Stop: {best['Stop']}")
    st.write(f"Target: {best['Target']}")
    st.write(f"Shares (1% Risk): {best['Shares (1%)']}")

    st.divider()
    st.write("### 📊 Signal Heatmap")
    st.dataframe(df_results)

else:
    st.warning("No signals available.")

time.sleep(60)
st.rerun()
