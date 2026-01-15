from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
import pymysql
import redis
import os
import json
import base64
import requests

app = Flask(__name__)
app.secret_key = 'TMEAS_DISTRIBUTED_SECURE_KEY_2026'
oauth = OAuth(app)

# Redis Connection 
r = redis.StrictRedis(
    host='master.tmeas-redis-cluster.u1kzxf.use1.cache.amazonaws.com',
    port=6379,
    ssl=True,
    decode_responses=True
)

# RDS Connection
def get_db():
    return pymysql.connect(
        host='tmeas-database.c2ve0sisuaoc.us-east-1.rds.amazonaws.com',
        user='admin',
        password='p|1O7HOVS(KaBp7$QQ6Sl64#c4r4',
        database='ecommerce',
        cursorclass=pymysql.cursors.DictCursor
    )

# AUTHENTICATION SETUP (Cognito OIDC)

oauth.register(
    name='oidc',
    authority='https://cognito-idp.us-east-1.amazonaws.com/us-east-1_BLCw9MClO',
    client_id='5a5pcpl5i7sm9hh8rirh4mj9l3',
    client_secret='k8pgm289hd5m56i2auf0anoggfn3idv7gch0k48r3aco12sbq5h',
    server_metadata_url='https://cognito-idp.us-east-1.amazonaws.com/us-east-1_BLCw9MClO/.well-known/openid-configuration',
    client_kwargs={'scope': 'email openid phone'}
)

# Helper: Read ALB Cognito Headers if present
def get_user_from_alb_header():
    encoded_jwt = request.headers.get('X-Amzn-Oidc-Data')
    if not encoded_jwt:
        return None
    try:
        payload = encoded_jwt.split('.')[1]
        decoded_payload = base64.b64decode(payload + "==").decode("utf-8")
        return json.loads(decoded_payload)
    except:
        return None

# Routes (Function)
@app.route('/')
def index():
    # Detect which server is handling this request for your assignment proof
    az = "Zone A"
    server_name = f"WebServer ({az})"

    # Identity Logic: Check ALB Header first, then Flask Session
    user_data = get_user_from_alb_header()
    if user_data:
        session['user'] = {'email': user_data.get('email')}
    user = session.get('user')

    # Redis (Cache)
    try:
        db_conn = get_db()
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM products")
            products = cursor.fetchall()
        db_conn.close()

        for p in products:
            redis_key = f"stock:{p['id']}"
            live_stock = r.get(redis_key)
            
            if live_stock is None:
                # Cache-Aside: Fetch from MySQL and write to Redis
                r.setnx(redis_key, p['quantity'])
                p['display_stock'] = p['quantity']
            else:
                p['display_stock'] = live_stock
    except Exception as e:
        print(f"Error loading products: {e}")
        products = []

    return render_template('index.html', user=user, products=products, server=server_name)

@app.route('/login')
def login():
    redirect_uri = 'https://tmeas-loadbalancer-1131116093.us-east-1.elb.amazonaws.com/authorize'
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
    session.clear()
#    return redirect('/')
    client_id = '5a5pcpl5i7sm9hh8rirh4mj9l3'
    logout_uri = 'https://tmeas-loadbalancer-1131116093.us-east-1.elb.amazonaws.com/'
    cognito_domain = 'https://us-east-1tlctqr8tp.auth.us-east-1.amazoncognito.com'

    cognito_logout_url = (
        f"{cognito_domain}/logout?"
        f"client_id={client_id}&"
        f"logout_uri={logout_uri}"
    )

    return redirect(cognito_logout_url)

@app.route('/buy/<int:product_id>', methods=['POST'])
def buy(product_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_email = session['user']['email']
    redis_key = f"stock:{product_id}"

    # atomic redis decr
    remaining = r.decr(redis_key)

    if remaining < 0:
        r.set(redis_key, 0) # Keep it at zero
        return "<h1>Error: Out of Stock!</h1><a href='/'>Go Back</a>"

    # Persistent record into mysql
    try:
        db_conn = get_db()
        with db_conn.cursor() as cursor:
            sql = "INSERT INTO orders (user_email, product_id, status) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_email, product_id, 'completed'))
            
            #Update quantity for products
            product_sql = "UPDATE products SET quantity = quantity - 1 WHERE id = %s AND quantity > 0"
            cursor.execute(product_sql, (product_id,))
        db_conn.commit()
        db_conn.close()
        
        # Redirect to confirmation to prevent form resubmission/404 on refresh
        return redirect(url_for('confirm_order', p_id=product_id))
    except Exception as e:
        r.incr(redis_key) # Rollback stock if DB fails
        return f"<h1>Database Error:</h1><p>{e}</p>"

@app.route('/confirm/<int:p_id>')
def confirm_order(p_id):
    return render_template('confirm.html', product_id=p_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
