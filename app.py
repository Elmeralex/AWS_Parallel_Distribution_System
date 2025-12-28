from flask import Flask, redirect, url_for, session, render_template
from authlib.integrations.flask_client import OAuth
import pymysql
import redis
import os

app = Flask(__name__)
app.secret_key = 'TMEAS_DISTRIBUTED_SECURE_KEY_2025_XYZ'
#app.secret_key = os.urandom(24)  # Use a secure random key in production
oauth = OAuth(app)

# --- 1. SHARED DATA TIER CONNECTIONS ---

# Redis Connection (Kept outside because Redis handles persistent connections well)
r = redis.StrictRedis(
    host='master.tmeas-redis-cluster.ks1nij.use1.cache.amazonaws.com',
    port=6379,
    ssl=True,
    decode_responses=True
)

# Function to get a fresh DB connection (Fixes the 500 error after idling)
def get_db():
    return pymysql.connect(
        host='tmeas-database.cluster-cal1sou8l5ld.us-east-1.rds.amazonaws.com',
        user='admin',
        password='8J8vO<g[$)A0>*QEEX~9R9sb3Ld<',
        database='ecommerce',
        cursorclass=pymysql.cursors.DictCursor
    )

# --- 2. AUTHENTICATION SETUP ---

oauth.register(
    name='oidc',
    authority='https://cognito-idp.us-east-1.amazonaws.com/us-east-1_BLCw9MClO',
    client_id='7cbnom28u9uouknu58h23kghd9',
    client_secret='fkcvc3f110i2f3jd48dhmkopv851bkd2clnt5dmj9daug8maqqe',
    server_metadata_url='https://cognito-idp.us-east-1.amazonaws.com/us-east-1_BLCw9MClO/.well-known/openid-configuration',
    client_kwargs={'scope': 'email openid phone'}
)

# --- 3. ROUTES ---

@app.route('/')
def index():
    user = session.get('user')
    # Fetch stock from shared Redis
    try:
        stock_count = r.get('laptop_stock') or 0
    except Exception as e:
        print(f"Redis Error: {e}")
        stock_count = "N/A"
    
    if user:
        return render_template('index.html', user=user, stock=stock_count)
    return 'Welcome! Please <a href="/login">Login</a>.'

@app.route('/login')
def login():
    redirect_uri = 'https://tmeas-loadbalancer-48856299.us-east-1.elb.amazonaws.com/authorize'
    return oauth.oidc.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = oauth.oidc.authorize_access_token()
    user = token.get('userinfo')
    if user:
        session['user'] = user
        session.permanent = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/buy', methods=['POST'])
def buy():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_email = session['user']['email']
    product_id = "laptop_01"

    # 1. ATOMIC REDIS DECREMENT
    remaining_stock = r.decr('laptop_stock')

    if remaining_stock < 0:
        r.set('laptop_stock', 0)
        return "<h1>Error: Out of Stock!</h1><a href='/'>Go Back</a>"

    # 2. PERSISTENT MYSQL RECORD (Uses fresh connection)
    try:
        db_conn = get_db()
        with db_conn.cursor() as cursor:
            sql = "INSERT INTO orders (user_email, product_id, status) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_email, product_id, 'completed'))
        db_conn.commit()
        db_conn.close()
    except Exception as e:
        print(f"Database Error: {e}")
        return f"<h1>Error:</h1><p>Stock was reserved, but DB failed: {e}</p>"

    return f"<h1>Success!</h1><p>Order recorded for {user_email}. New stock: {remaining_stock}</p><a href='/'>Continue Shopping</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
