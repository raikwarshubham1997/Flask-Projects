
from curses import flash
from unittest import result
from flask import Flask, request, session,render_template, redirect, url_for
from flaskext.mysql import MySQL
from flask_bcrypt import Bcrypt
import pymysql
#import regex 
import re 
import uuid

app = Flask(__name__)

app.secret_key = 'cairocoders-ednalan'
bcrypt = Bcrypt(app)
mysql = MySQL()

# mysql configratipons
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'testsql'
app.config['MYSQL_DATABASE_CHARSET'] = 'utf-8'
mysql.init_app(app)

# http://localhost:5000/pythonlogin/ - this will be the login page
@app.route('/pythonlogin/', methods =['GET', 'POST'])
def login():
    # connect
    conn = pymysql.connect(host='localhost', port=3306, user='root',
    passwd='',db='testsql', charset="utf8")
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # output message if something goes wrong...
    msg = ''
    # check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        # Check if account exist using MySQL
        cursor.execute('SELECT * FROM account WHERE username = % s AND password = % s', (username, password, ))
        # fetch one record and return result
        account = cursor.fetchone()
        
        # if account exists in account table in out database
        if account:
            # create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # redirect to home page
            msg = 'Logged in successfully !'
            return render_template('home.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)


# http://localhost:5000/register - this will be the registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
 # connect
    conn = pymysql.connect(host='localhost', port=3306, user='root',
    passwd='',db='testsql', charset="utf8")
    cursor = conn.cursor(pymysql.cursors.DictCursor)
  
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
   
        #Check if account exists using MySQL
        cursor.execute('SELECT * FROM account WHERE username = %s', (username))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into account table
            cursor.execute('INSERT INTO account VALUES (NULL, %s, %s, %s, %s)', (fullname, username, password, email)) 
            conn.commit()
   
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)
  
# http://localhost:5000/home - this will be the home page, only accessible for loggedin users
@app.route('/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
   
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
  
# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))
 
# http://localhost:5000/profile - this will be the profile page, only accessible for loggedin users
@app.route('/profile')
def profile(): 
 # Check if account exists using MySQL
    conn = pymysql.connect(host='localhost', port=3306, user='root',
    passwd='',db='testsql', charset="utf8")
    cursor = conn.cursor(pymysql.cursors.DictCursor)
  
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor.execute('SELECT * FROM account WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    conn = pymysql.connect(host='localhost', port=3306, user='root',
    passwd='',db='testsql', charset="utf8")
    if 'loggedin' in session:
        return redirect("/")
    if request.method == "POST":
        email = request.form['email']
        token = str(uuid.uuid4())
        cur = conn.cursor()
        result = cur.execute("SELECT * FROM account WHERE email=%s", [email])
        if result > 0:
            data = cur.fetchone()
            cur = conn.cursor()
            cur.execute("UPDATE account SET token=%s WHERE email=%s", [token, email])

            conn.commit()
            cur.close()
            
            return render_template("reset_request.html")
        else:
            return render_template("/")
    return render_template("reset_request.html")

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    conn = pymysql.connect(host='localhost', port=3306, user='root',
    passwd='',db='testsql', charset="utf8")
    if 'loggedin' in session:
        return redirect("/")
    if request.method == "POST":
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        token1 = str(uuid.uuid4())
        if password != confirm_password:
            # flash("Password do not match", 'danger')
            return render_template("/reset")
        password = bcrypt.generate_password_hash(password)
        cur = conn.cursor()
        cur.execute("SELECT * FROM account WHERE token=%s", [token])
        user = cur.fetchone()
        if user:
            cur = conn.cursor()
            cur.execute("UPDATE account SET token=%s, password=%s WHERE email=%s", [token1, password, token])

            conn.commit()
            cur.close()
            # flash("Your password successfully updated", 'success')
            return render_template("reset.html")
        # else:
        #     flash("Your token is invalid", 'danger')
            
    return render_template("reset.html")
        



if __name__ == '__main__':
    app.run(debug=True)