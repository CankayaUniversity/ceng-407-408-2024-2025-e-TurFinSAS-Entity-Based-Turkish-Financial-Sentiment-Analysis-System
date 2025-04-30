from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from werkzeug.utils import secure_filename
import yfinance as yf
from flask_caching import Cache
from datetime import datetime
from flask_migrate import Migrate


app = Flask(__name__)
app.secret_key = 'kral-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 900})  # 900 saniye = 15 dk

bist100_symbols = [
    "AEFES.IS", "AGHOL.IS", "AKBNK.IS", "AKCNS.IS", "AKSA.IS",
    "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ARCLK.IS", "ASELS.IS",
    "ASTOR.IS", "AYDEM.IS", "BIMAS.IS", "BIOEN.IS", "BRISA.IS",
    "BRSAN.IS", "CIMSA.IS", "DOAS.IS", "DOHOL.IS", "ECILC.IS",
    "EGEEN.IS", "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "EREGL.IS",
    "ESEN.IS", "FROTO.IS", "GARAN.IS", "GESAN.IS", "GUBRF.IS",
    "GWIND.IS", "HEKTS.IS", "ISCTR.IS", "ISGYO.IS", "KARSN.IS",
    "KCHOL.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMD.IS",
    "MAVI.IS", "MGROS.IS", "ODAS.IS", "OTKAR.IS", "OYAKC.IS",
    "PENTA.IS", "PETKM.IS", "PGSUS.IS", "QUAGR.IS", "SAHOL.IS",
    "SASA.IS", "SISE.IS", "SKBNK.IS", "SMRTG.IS", "SOKM.IS",
    "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS", "TOASO.IS",
    "TRGYO.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS",
    "TUKAS.IS", "TUPRS.IS", "ULKER.IS", "VAKBN.IS", "VESTL.IS",
    "VERTU.IS", "YEOTK.IS", "YKBNK.IS", "ZOREN.IS", "ARDYZ.IS",
    "BAYRK.IS", "BERA.IS", "CANTE.IS", "CWENE.IS", "DERIM.IS",
    "DOBUR.IS", "DGNMO.IS", "EKSUN.IS", "FLAP.IS", "INFO.IS",
    "KMPUR.IS", "KONTR.IS", "KRONT.IS", "KZBGY.IS", "LIDFA.IS",
    "MAKTK.IS", "OZRDN.IS", "PAPIL.IS", "QNBTR.IS", "RALYH.IS",
    "SANEL.IS", "TMSN.IS", "INTEK.IS", "YATAS.IS", "YYLGD.IS"
]

user_favorites = db.Table('user_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('symbol', db.String(20), db.ForeignKey('favorite_stock.symbol'), primary_key=True)
)


def fetch_bist100_data(symbols):
    results = []
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info

            unix_time = info.get("regularMarketTime")
            formatted_time = datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S') if unix_time else "N/A"

            results.append({
                "name": info.get("shortName", symbol),
                "price": info.get("currentPrice"),
                "symbol": symbol,
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", 0),
                "time": formatted_time
            })
        except Exception as e:
            print(f"Hata: {symbol} -> {e}")
    return results


@cache.cached(timeout=900, key_prefix='bist_data')  # 15 dakikalık cache
def get_cached_bist_data():
    return fetch_bist100_data(bist100_symbols)

def fetch_chart_data(symbol):
    import yfinance as yf
    import pandas as pd

    stock = yf.Ticker(symbol)
    hist = stock.history(period="1y")  # 1 yıllık veri
    hist = hist.reset_index()
    return {
        "label": symbol,
        "dates": hist['Date'].dt.strftime('%Y-%m-%d').tolist(),
        "prices": hist['Close'].round(2).tolist(),
        "latest_price": round(hist['Close'].iloc[-1], 2),
        "percent_change": round(((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100, 2)
    }

def get_stock_chart_data(symbol, period="6mo"):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)

        prices = hist["Close"].tolist()
        dates = [d.strftime("%Y-%m-%d") for d in hist.index]

        return {
            "label": symbol,
            "prices": prices,
            "dates": dates,
            "latest_price": round(prices[-1], 2) if prices else 0,
            "percent_change": round(((prices[-1] - prices[0]) / prices[0]) * 100, 2) if prices else 0
        }
    except Exception as e:
        print(f"[HATA] Veri çekilirken hata oluştu: {e}")
        return {
            "label": symbol,
            "prices": [],
            "dates": [],
            "latest_price": 0,
            "percent_change": 0
        }



# Kullanıcı Modeli
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    role = db.Column(db.String(50), default='user')
    profile_picture = db.Column(db.String(150))

    favorites = db.relationship(
        'FavoriteStock',
        secondary=user_favorites,
        backref=db.backref('users', lazy='dynamic'),
        lazy='dynamic'
    )

class FavoriteStock(db.Model):
    __tablename__ = 'favorite_stock'
    symbol = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(150))

# Profil fotosu ekleme
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Klasör yoksa oluştur
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/delete-user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash("Bu işlem için yetkin yok!", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    if user.username == current_user.username:
        flash("Kendini silemezsin kral!", "warning")
        return redirect(url_for('admin_panel'))

    db.session.delete(user)
    db.session.commit()
    flash("Kullanıcı başarıyla silindi!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/update-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    if current_user.role != 'admin':
        flash("Yetkin yok!", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']

        file = request.files.get('profile_picture')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.profile_picture = filename

        user.username = username
        user.role = role
        db.session.commit()
        flash("Kullanıcı güncellendi!", "success")
        return redirect(url_for('admin_panel'))

    return render_template('update_user.html', user=user)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        uname = request.form['username']
        new_pass = request.form['new_password']
        user = User.query.filter_by(username=uname).first()

        if not user:
            flash("Bu kullanıcı bulunamadı!", "danger")
            return redirect(url_for('reset_password'))

        if len(new_pass) < 6:
            flash("Yeni şifre en az 6 karakter olmalı!", "warning")
            return redirect(url_for('reset_password'))

        user.password = generate_password_hash(new_pass)
        db.session.commit()
        flash("Şifre başarıyla sıfırlandı. Giriş yapabilirsin.", "success")
        return redirect(url_for('login'))

    return render_template('reset_password.html')


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username'].strip()
        passwd = request.form['password'].strip()
        file = request.files.get('profile_picture')
        filename = None

        # Doğrulama
        if len(uname) < 3:
            flash("Kullanıcı adı en az 3 karakter olmalı!", "warning")
            return redirect(url_for('register'))

        if len(passwd) < 6:
            flash("Şifre en az 6 karakter olmalı!", "warning")
            return redirect(url_for('register'))

        if User.query.filter_by(username=uname).first():
            flash("Bu kullanıcı adı zaten alınmış!", "danger")
            return redirect(url_for('register'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        hashed_pw = generate_password_hash(passwd)
        role = 'admin' if 'admin' in uname.lower() else 'user'

        new_user = User(username=uname, password=hashed_pw, role=role, profile_picture=filename)
        db.session.add(new_user)
        db.session.commit()
        flash("Kayıt başarılı! Şimdi giriş yapabilirsin.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Admin yetkisi gerekli!", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function
@app.route('/admin-panel')
@admin_required
def admin_panel():
    users = User.query.all()

    stats = {
        'total': len(users),
        'admins': sum(1 for u in users if u.role == 'admin'),
        'regulars': sum(1 for u in users if u.role == 'user')
    }

    return render_template('admin.html', users=users, stats=stats)




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        passwd = request.form['password']
        user = User.query.filter_by(username=uname).first()

        if user and check_password_hash(user.password, passwd):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Kullanıcı adı veya şifre hatalı!", "danger")

    return render_template('login.html')



@app.route('/dashboard', methods=["GET", "POST"])
@login_required
def dashboard():
    if current_user.role == 'admin':
        mesaj = f"👑 Hoş geldin {current_user.username}! Yönetici paneline hoş geldin."
    else:
        mesaj = f"Merhaba {current_user.username}, iyi ki geldin! 👋"

    bist_data = get_cached_bist_data()
    symbols = [h["symbol"] for h in bist_data]

    selected_1 = request.form.get("symbol1")
    selected_2 = request.form.get("symbol2")

    data1 = fetch_chart_data(selected_1) if selected_1 else None
    data2 = fetch_chart_data(selected_2) if selected_2 else None

    detail_symbol = request.form.get("detail_symbol")
    detail_range = request.form.get("detail_range", "1y")
    detail_data = None
    if request.form.get("tab") == "detail" and detail_symbol:
        detail_data = get_stock_chart_data(detail_symbol, period=detail_range)

    favori_semboller = [s.symbol for s in current_user.favorites]
    favorilerim = fetch_bist100_data(favori_semboller)

    active_tab = request.args.get("tab") or request.form.get("tab") or "list"

    return render_template(
        'dashboard.html',
        mesaj=mesaj,
        is_admin=current_user.role == 'admin',
        profile_picture=current_user.profile_picture,
        bist_data=bist_data,
        symbols=symbols,
        selected_1=selected_1,
        selected_2=selected_2,
        data1=data1,
        data2=data2,
        favori_semboller=favori_semboller,
        favorilerim=favorilerim,
        active_tab=active_tab,
        selected_detail_symbol = detail_symbol,
        selected_detail_range=detail_range,
        detail_data = detail_data,
    )


@app.route('/compare', methods=['GET', 'POST'])
@login_required
def compare():
    bist100_symbols = ["AKBNK.IS", "ASELS.IS", "SISE.IS", "KCHOL.IS", "ISCTR.IS", "THYAO.IS", "FROTO.IS"]  # örnek liste

    selected_1 = request.form.get("symbol1")
    selected_2 = request.form.get("symbol2")
    data1 = data2 = []

    if selected_1 and selected_2:
        data1 = fetch_chart_data(selected_1)
        data2 = fetch_chart_data(selected_2)

    return render_template("compare.html",
                           symbols=bist100_symbols,
                           selected_1=selected_1,
                           selected_2=selected_2,
                           data1=data1,
                           data2=data2)

@app.route('/toggle-favorite/<symbol>', methods=['POST'])
@login_required
def toggle_favorite(symbol):
    stock = FavoriteStock.query.get(symbol)
    if not stock:
        stock = FavoriteStock(symbol=symbol)
        db.session.add(stock)

    is_favorite = current_user.favorites.filter_by(symbol=symbol).first()
    if is_favorite:
        current_user.favorites.remove(stock)
        db.session.commit()
        return jsonify({'status': 'removed'})
    else:
        current_user.favorites.append(stock)
        db.session.commit()
        return jsonify({'status': 'added'})



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Çıkış yaptın!", "info")
    return redirect(url_for('login'))

# Hata mesajları için
@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

@app.errorhandler(401)
def unauthorized(e):
    flash("Bu sayfaya erişmek için giriş yapmalısın!", "warning")
    return redirect(url_for('login'))

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403



with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
