from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import itertools
#from app import mysql, app


app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '789123'
app.config['MYSQL_DB'] = 'mywikiapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

#Articles = Articles()

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
    role = StringField('Role', [validators.Length(min=1, max=50)])


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        role = form.role.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password, role) VALUES(%s, %s, %s, %s, %s)", (name, email, username, password, role))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        #cur.execute("SELECT role FROM users WHERE username = %s", [username])
        #role = cur.fetchone()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
       
        
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')

                if data['role'] == 'admin':
                    return redirect(url_for('index'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')
    

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Index
@app.route('/')
#@is_logged_in
def index():
    role = None
    try:
        if session['logged_in']:
            #create cursor
            cur = mysql.connection.cursor()
            #Get user role
            cur.execute("SELECT role FROM users WHERE username = %s", [session['username']])
            role = cur.fetchone()
            cur.close()
    except KeyError:
        next
    return render_template('home.html', userrole = role )


# About
@app.route('/about')
def about():
    return render_template('about.html')



# Articles
@app.route('/articles', methods= ['POST', 'GET'])
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        search = request.form['article']

        result = cur.execute('SELECT *FROM articles where title LIKE %s OR author LIKE %s', ('%'+search+'%', '%'+search+'%'))

        articles = cur.fetchall()

        #return render_template('search_result.html', articles = articles)

    else:

        # Get articles
        result = cur.execute("SELECT * FROM articles")

        articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in 

    editor = 'editor'
    cur.execute("SELECT username FROM users WHERE role = %s", [editor])
    lt = cur.fetchall()
    username = list(itertools.chain(*lt))

    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        
        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()
        
        #Close connection
        cur.close()

        #Create Cursor
        cur = mysql.connection.cursor()

        #Execute 
        cur.execute("INSERT into edits(username, article) values(%s, %s)", (session['username'], title))

        #Commit Changes
        mysql.connection.commit()

        #Close connection
        cur.close()
        
        flash('Article Created will be approved by the admin', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    #Fetch article
    article = cur.fetchone()
    
    #close cursor
    cur.close()

    cur = mysql.connection.cursor()

    title = article['title']

    #Execute
    cur.execute("INSERT INTO edits(username, article) VALUES(%s, %s)", (session['username'], title))

    #Commit Changes
    mysql.connection.commit()

    #Close
    cur.close()

    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s  WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

@app.route('/edits')
@is_logged_in
def edits():
    #create sursor
    cur = mysql.connection.cursor()

    results = cur.execute("SELECT * FROM edits")

    logs = cur.fetchall()

    if results > 0:

        return render_template('edits.html', edits_logs = logs)
    
    else: 
        msg = 'No Edit history'
        return render_template('edits.html', msg = msg)

    


@app.route('/clear_edit', methods= ['POST'])
@is_logged_in
def clear():

    cur = mysql.connection.cursor()

    cur.execute('TRUNCATE TABLE edits')

    mysql.connection.commit()

    cur.close()

    flash('Cleared edit logs', 'success')

    return redirect(url_for('index'))

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))

#admin page
@app.route('/reviews',methods=['POST', 'GET'])
@is_logged_in
def reviews():
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('reviews.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('reviews.html', msg=msg)
    # Close connection
    cur.close()


class statusform(Form):
   status = StringField('Status(approved/reject)', [validators.Length(min=1, max=30)]) 

@app.route('/review/<string:id>', methods=['GET','POST'])
@is_logged_in
def review(id):
    
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    #Close connection
    cur.close()

    form = statusform(request.form)
    if request.method == 'POST' and form.validate():
        status =  form.status.data

        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET status=%s WHERE id = %s", (status, id))
        # Commit to DB
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('articles'))
    
    return render_template('review.html', article=article, form=form)


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
