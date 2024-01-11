
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, jsonify
from flaskext.mysql import MySQL
import pymysql,requests
import mysql.connector
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.secret_key = "elaundry_db"

mysql = MySQL()

API_KEY = 'fca_live_eSP74XCEzTfP2eJ3TNFAO8JV1h1aVxNcwTVfnG64'
BASE_URL = 'https://open.er-api.com/v6/latest'

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'elaundry_db'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


class RegisterForm(Form):
    name = StringField('Nama', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    phone = StringField('Nomer Handphone', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


API_KEY = 'fca_live_eSP74XCEzTfP2eJ3TNFAO8JV1h1aVxNcwTVfnG64'
BASE_URL = 'https://open.er-api.com/v6/latest'


@app.route('/convert', methods=['POST'])
def convert():
    from_currency = request.form['from_currency']
    to_currency = request.form['to_currency']
    amount = float(request.form['amount'])

    result = perform_conversion(from_currency, to_currency, amount)
    return render_template('beranda.html', result=result, currencies=get_supported_currencies())

def get_supported_currencies():
    response = requests.get(BASE_URL + f'?apikey={API_KEY}')
    data = response.json()
    currencies = list(data['rates'].keys())
    currencies.sort()
    return currencies

def perform_conversion(from_currency, to_currency, amount):
    response = requests.get(f'{BASE_URL}/{from_currency}?apikey={API_KEY}')
    data = response.json()

    if 'error' in data:
        return {'error': data['error']['info']}

    try:
        rates = data['rates']
    except KeyError:
        print(f"Unexpected API response: {data}")
        return {'error': 'Failed to fetch exchange rates for the selected currencies.'}

    try:
        rate = rates[to_currency]
        converted_amount = round(amount * rate, 2)

        result = {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'amount': amount,
            'converted_amount': converted_amount,
            'rate': rate
        }

        return result
    except KeyError:
        return {'error': f'Failed to find exchange rate for {to_currency} in the API response.'}
    
@app.route('/')
def index():
    return render_template('home.html')


@app.route('/beranda')
def beranda():
    currencies = get_supported_currencies()
    return render_template('beranda.html', currencies=currencies)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        phone = form.phone.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        conn = mysql.connect()
        cur = conn.cursor(pymysql.cursors.DictCursor)
     
        cur.execute("INSERT INTO user(name, email, phone, username, password) VALUES(%s, %s, %s, %s, %s)", (name, email, phone, username, password))
    
        conn.commit()
     
        cur.close()
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password_candidate = request.form['password']

        conn = mysql.connect()
        cur = conn.cursor(pymysql.cursors.DictCursor)

 
        result = cur.execute("SELECT * FROM user WHERE username = %s", [username])

        if result > 0:
     
            data = cur.fetchone()
            password = data['password']


            if sha256_crypt.verify(password_candidate, password):
        
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('beranda'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')
    

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/service')
def service():
    return render_template('service.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)

