from flask import Flask, redirect, render_template, request, make_response, session, abort, jsonify, url_for
import secrets
from functools import wraps
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import timedelta
import os
from dotenv import load_dotenv
import yfinance as yf

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

bist100_symbols = [
    "AEFES.IS", "AGHOL.IS", "AKBNK.IS", "AKCNS.IS", "AKSA.IS", "AKSEN.IS",
    "ALARK.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", "BIOEN.IS",
    "BRISA.IS", "CIMSA.IS", "DOAS.IS", "ECILC.IS", "EGEEN.IS", "EREGL.IS",
    "FROTO.IS", "GARAN.IS", "GESAN.IS", "GUBRF.IS", "HEKTS.IS", "ISCTR.IS",
    "KCHOL.IS", "KRDMD.IS", "MAVI.IS", "MGROS.IS", "PETKM.IS", "PGSUS.IS",
    "SAHOL.IS", "SASA.IS", "SISE.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS",
    "TKFEN.IS", "TOASO.IS", "TUPRS.IS", "ULKER.IS", "VAKBN.IS", "VESTL.IS",
    "YKBNK.IS", "ZOREN.IS"
]


def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if 'user' not in session:
            return redirect(url_for('login'))

        else:
            return f(*args, **kwargs)

    return decorated_function


@app.route('/auth', methods=['POST'])
def authorize():
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return "Unauthorized", 401

    token = token[7:]  # Strip off 'Bearer ' to get the actual token

    try:
        decoded_token = auth.verify_id_token(token, check_revoked=True, clock_skew_seconds=60)  # Validate token here
        session['user'] = decoded_token  # Add user to session
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
    else:
        return render_template('login.html')

@app.route('/signup')
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('signup.html')


@app.route('/reset-password')
def reset_password():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('forgot_password.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove the user from session
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)  # Optionally clear the session cookie
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
            })
        except Exception as e:
            print(f"[HATA] {symbol}: {e}")
    return results

@app.route('/dashboard', methods=['GET', 'POST'])
@auth_required
def dashboard():
    user_id = session['user']['uid']
    user_doc = db.collection('users').document(user_id).get()
    favori_semboller = user_doc.to_dict().get('favorites', []) if user_doc.exists else []
    bist_data = fetch_bist100_data(bist100_symbols)
    favorilerim = fetch_bist100_data(favori_semboller)
    return render_template('dashboard.html',
                           bist_data=bist_data,
                           favori_semboller=favori_semboller,
                           favorilerim=favorilerim,
                           username=session['user']['name'])

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
