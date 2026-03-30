import os
from flask import Flask, request, redirect
from models import db,URL
import string, random
from datetime import datetime, timedelta
from flask import render_template

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        short_code = ''.join(random.choice(chars) for _ in range(length))
        
        # ensure uniqueness
        if not URL.query.filter_by(short_code=short_code).first():
            return short_code

app = Flask(__name__)

# 🔗 Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db.init_app(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.form.get('url')
    if not original_url.startswith("http://") and not original_url.startswith("https://"):
        original_url = "http://" + original_url
    expiry = request.form.get('expiry')

    if not original_url:
        return "Invalid URL"

    custom = request.form.get('custom')

    if custom:
        # check if already exists
        existing = URL.query.filter_by(short_code=custom).first()
        if existing:
            return "Custom URL already taken ❌"
        short_code = custom
    else:
        short_code = generate_short_code()
    expires_at = None
    if expiry:
        expires_at = datetime.utcnow() + timedelta(minutes=int(expiry))

    new_url = URL(
        original_url=original_url,
        short_code=short_code,
        expires_at=expires_at
    )

    db.session.add(new_url)
    db.session.commit()

    return render_template('results.html', short_code=short_code)
@app.route('/<short_code>')
def redirect_url(short_code):
    url = URL.query.filter_by(short_code=short_code).first()

    if not url:
        return "Invalid short URL ❌"

    # 🔥 expiry check
    if url.expires_at and datetime.utcnow() > url.expires_at:
        return "This link has expired ⏳"

    # 📊 increment clicks
    url.clicks += 1
    db.session.commit()

    return redirect(url.original_url)

@app.route('/dashboard')
def dashboard():
    urls = URL.query.all()
    return render_template('dashboard.html', urls=urls)

# Create DB file automatically
with app.app_context():
    db.create_all()


    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))