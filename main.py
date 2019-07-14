from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:1234@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
app.secret_key = 'zaq1xsw2cde3'


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    content = db.Column(db.Text())
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, content, owner):
        self.title = title
        self.content = content
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(120), unique = True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref = 'owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['logon', 'register', 'index', 'blog_listing']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/register')

@app.route('/', methods=['POST', 'GET'])
def index():
    users = User.query.all()
    return render_template('index.html', users = users)

@app.route('/blog', methods=['POST', 'GET'])
def blog_listing():
    title = "Blog"

    if session:
        owner = User.query.filter_by(username = session['username']).first()

    if "id" in request.args:
        post_id = request.args.get('id')
        blog = Blog.query.filter_by(id = post_id).all()
        # username = User.query.get(owner.username)
        return render_template('blog.html', title = title, blog = blog, post_id = post_id)

    elif "user" in request.args:
        user_id = request.args.get('user')
        blog = Blog.query.filter_by(owner_id = user_id).all()
        return render_template('blog.html', title = title, blog = blog)

    else:
        blog = Blog.query.order_by(Blog.id.desc()).all()
        return render_template('blog.html', title = title, blog = blog)

@app.route('/logon', methods=['POST', 'GET'])
def logon():
    username = ""
    username_error = ""
    password_error = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()

        if not user:
            username_error = "This user does not exist."
            if username == "":
                username_error = "Please enter your username."

        if password == "":
            password_error = "Please enter your password."

        if user and user.password != password:
            password_error = "This password is incorrect!"

        if user and user.password == password:
            session['username'] = username
            return redirect('/newpost')

    return render_template('logon.html', username = username, username_error = username_error, password_error = password_error)

@app.route('/register', methods=['POST', 'GET'])
def register():
    username = ""
    username_error = ""
    password_error = ""
    verify_error = ""

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        existing_user = User.query.filter_by(username = username).first()

        if len(username) < 3:
            username_error = "Usernames must be longer than 3 characters."
            if username == "":
                username_error = "Please enter a username."

        if password != verify:
            password_error = "Passwords do not match."
            verify_error = "Passwords do not match."
            
        if len(password) < 3:
            password_error = "Password must be longer than 3 characters."
            if password == "":
                password_error = "A valid password is needed to continue."

        if password != verify:
            password_error = "Passwords do not match."
            verify_error = "Passwords do not match."

        if not username_error and not password_error and not verify_error:
            if not existing_user:
                new_user = User(username, password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                return redirect('/newpost')
            else:
                username_error = "Please enter a unique username."

    return render_template('register.html', username = username, username_error = username_error, password_error = password_error, verify_error = verify_error)

@app.route('/newpost', methods=['POST', 'GET'])
def create_new_post():
    blog_title = ""
    blog_content = ""
    title_error = ""
    content_error = ""
    owner = User.query.filter_by(username = session['username']).first()

    if request.method == 'POST':
        blog_title = request.form['blog_title']
        blog_content = request.form['blog_content']

        if blog_title == "":
            title_error = "You Forgot you title!"

        if blog_content == "":
            content_error = "A post is needed to Continue!"

        if title_error == "" and content_error == "":
            new_post = Blog(blog_title, blog_content, owner)
            db.session.add(new_post)
            db.session.commit()
            blog_id = Blog.query.order_by(Blog.id.desc()).first()
            user = owner

            return redirect('/blog?id={}&user={}'.format(blog_id.id, user.username))

    return render_template('newpost.html', title = "Add a new post", blog_title = blog_title, blog_content = blog_content, title_error = title_error, content_error = content_error)

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

if __name__ == "__main__":
    app.run()