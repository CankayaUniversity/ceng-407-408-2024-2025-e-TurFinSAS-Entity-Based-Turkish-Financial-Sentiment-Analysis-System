# Model tahmini için gerekli ek kütüphaneler
import pandas as pd
import xgboost as xgb
import joblib
import numpy as np
from flask import Flask, redirect, render_template, request, make_response, session, abort, jsonify, url_for
import secrets
from functools import wraps
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import timedelta
import os
from dotenv import load_dotenv
import yfinance as yf
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-kral-key')

# Session ayarları
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Firebase kurulum
cred = credentials.Certificate("firebase-auth.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

bist30_symbols = [
    "AEFES.IS", "AKBNK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", "CIMSA.IS",
    "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "HEKTS.IS",
    "ISCTR.IS", "KCHOL.IS", "KOZAL.IS", "KRDMD.IS", "MGROS.IS", "PETKM.IS",
    "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TAVHL.IS", "TCELL.IS",
    "THYAO.IS", "TOASO.IS", "TTKOM.IS", "TUPRS.IS", "ULKER.IS", "YKBNK.IS"
]

cached_bist_data = None

# Model ve scaler'ı yükle
model = xgb.XGBRegressor()
model.load_model("xgboost_trained_model.json")
scaler = joblib.load("scaler.pkl")

# Tahmin için kullanılacak özellik sırası
FEATURE_ORDER = ['num_news', 'avg_weight', 'news_perc_change', 'avg_weight_diff']

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/auth', methods=['POST'])
def authorize():
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return "Unauthorized", 401
    token = token[7:]
    try:
        decoded_token = auth.verify_id_token(token, check_revoked=True, clock_skew_seconds=60)
        session['user'] = decoded_token
        return redirect(url_for('dashboard'))
    except:
        return "Unauthorized", 401

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/signup')
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/reset-password')
def reset_password():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('forgot_password.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response

def fetch_bist100_data(symbols):
    results = []
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            results.append({
                "name": info.get("shortName", symbol),
                "price": info.get("currentPrice"),
                "symbol": symbol,
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", 0),
                "time": time.strftime("%H:%M")
            })
            time.sleep(2.5)
        except Exception as e:
            print(f"[HATA] {symbol}: {e}")
    return results

def get_symbol_data(symbol, period="1y"):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        label = stock.info.get("shortName", symbol)
        latest_price = stock.info.get("currentPrice", 0)
        change_percent = ((hist["Close"][-1] - hist["Close"][0]) / hist["Close"][0]) * 100
        return {
            "label": label,
            "latest_price": latest_price,
            "percent_change": round(change_percent, 2),
            "dates": hist.index.strftime("%Y-%m-%d").tolist(),
            "prices": hist["Close"].round(2).tolist()
        }
    except Exception as e:
        print(f"[HATA] get_symbol_data({symbol}): {e}")
        return None

@app.route('/dashboard', methods=['GET', 'POST'])
@auth_required
def dashboard():
    global cached_bist_data
    user_id = session['user']['uid']
    user_doc = db.collection('users').document(user_id).get()
    favori_semboller = user_doc.to_dict().get('favorites', []) if user_doc.exists else []

    if cached_bist_data is None:
        cached_bist_data = fetch_bist100_data(bist30_symbols)
        print("🔁 Hisse verisi ilk kez çekildi ve cache'e alındı.")

    favorilerim = fetch_bist100_data(favori_semboller)

    active_tab = request.form.get("tab") or request.args.get("tab") or "list"

    symbol1 = request.form.get("symbol1")
    symbol2 = request.form.get("symbol2")
    data1, data2 = None, None
    if active_tab == "compare" and symbol1 and symbol2:
        data1 = get_symbol_data(symbol1)
        data2 = get_symbol_data(symbol2)

    detail_symbol = request.form.get("detail_symbol")
    detail_range = request.form.get("detail_range", "1y")
    detail_data = None
    if active_tab == "detail" and detail_symbol:
        detail_data = get_symbol_data(detail_symbol, period=detail_range)

    ticker = request.form.get("ticker")
    result = None
    error = None
    tickers = []

    if active_tab == "predict":
        try:
            df = pd.read_csv("cleaned_bist30_sentiment_for_bilstm.csv")
            if "ticker" not in df.columns:
                raise Exception("CSV dosyasında 'ticker' sütunu bulunamadı.")
            df['affected_date'] = pd.to_datetime(df['affected_date'])
            tickers = sorted(df['ticker'].unique())

            if ticker:
                sub_df = df[df['ticker'] == ticker].sort_values(by='affected_date')
                if len(sub_df) < 2:
                    error = "Yeterli veri yok."
                else:
                    today = sub_df.iloc[-1]
                    yesterday = sub_df.iloc[-2]
                    num_news = today['num_news']
                    avg_weight = today['avg_weight']
                    prev_num_news = yesterday['num_news']
                    prev_avg_weight = yesterday['avg_weight']
                    news_perc_change = (num_news - prev_num_news) / prev_num_news if prev_num_news != 0 else 0
                    avg_weight_diff = avg_weight - prev_avg_weight
                    X_input = pd.DataFrame([[num_news, avg_weight, news_perc_change, avg_weight_diff]],
                                           columns=FEATURE_ORDER)
                    X_scaled = scaler.transform(X_input)
                    prediction = model.predict(X_scaled)[0]
                    result = round(prediction * 100, 2)
        except Exception as e:
            error = str(e)

    return render_template('dashboard.html',
        bist_data=cached_bist_data,
        favori_semboller=favori_semboller,
        favorilerim=favorilerim,
        symbols=bist30_symbols,
        username=session['user']['name'],
        active_tab=active_tab,
        selected_1=symbol1,
        selected_2=symbol2,
        data1=data1,
        data2=data2,
        detail_data=detail_data,
        selected_detail_symbol=detail_symbol,
        selected_detail_range=detail_range,
        result=result,
        error=error,
        tickers=tickers,
        selected_ticker=ticker
    )

@app.route('/toggle-favorite/<symbol>', methods=['POST'])
@auth_required
def toggle_favorite(symbol):
    user_id = session['user']['uid']
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        data = user_doc.to_dict()
        favorites = data.get('favorites', [])
        if symbol in favorites:
            favorites.remove(symbol)
            status = 'removed'
        else:
            favorites.append(symbol)
            status = 'added'
    else:
        favorites = [symbol]
        status = 'added'
    user_ref.set({'favorites': favorites}, merge=True)
    return jsonify({'status': status})

if __name__ == '__main__':
    app.run(host='localhost', port=5000)
