from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from wtforms import (Form, PasswordField, validators, StringField)
from hashutils import check_pw_hash, make_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://Blogz:launchcode@localhost:8889/Blogz'
app.config['SQLALCHEMY_ECHO'] = True
app.secret_key = "JCJhmvHSY9uURT2v"
db = SQLAlchemy(app)


class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    body = db.Column(db.String(300))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, body, owner):
        self.name = name
        self.body = body
        self.owner = owner


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, email, password):
        self.email = email
        self.password = password
        self.username = username


class LoginForm(Form):
    email = StringField(
        'Email Address', [
            validators.Email(message='Invalid Email address'),
            validators.DataRequired(),
            validators.Length(
                min=6,
                max=35,
                message='Must be between %(min)d and %(max)d characters.')
        ])
    password = PasswordField('Password', [validators.DataRequired()])


class RegistrationForm(Form):

    username = StringField('Username', [
        validators.DataRequired(),
        validators.Length(
            min=6,
            max=35,
            message='Must be between %(min)d and %(max)d characters.')
    ])
    email = StringField(
        'Email Address', [
            validators.Email(message='Invalid Email address'),
            validators.DataRequired(),
            validators.Length(
                min=6,
                max=35,
                message='Must be between %(min)d and %(max)d characters.')
        ])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'),
        validators.Length(
            min=8,
            max=35,
            message='Must be between %(min)d and %(max)d characters.')
    ])
    confirm = PasswordField('Confirm Password')


@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'blogs']
    #check for email in session dictionary, before responding to requests
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST':

        existing_user = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()

        if existing_user or existing_email:
            flash('User already exists!', 'error')

        elif form.validate() and not existing_user and not existing_email:

            username = str(form.username.data)
            email = str(form.email.data)
            password = str(form.password.data)
            password = make_pw_hash(password)

            new_user = User(username, email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            flash('Registered and logged in', "success")
            return redirect('./blog')
    return render_template(
        'register.html', form=form, title="Register", endpoint='/register')


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST':
        email = str(form.email.data)
        password = str(form.password.data)
        user = User.query.filter_by(email=email).first()
        if user and check_pw_hash(password, user.password):
            session['email'] = email
            flash('Logged in', "success")
            return redirect('/')
        else:
            flash('Password incorrect, or user does not exist', 'error')

    return render_template(
        'login.html', form=form, title="Log In", endpoint='/login')


@app.route('/logout')
def logout():
    del session['email']
    return redirect('/login')


@app.route("/newblog", methods=['POST', 'GET'])
def newblog():
    owner = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        blog_name = request.form['blog-name']
        blog_body = request.form['blog-body']

        if blog_name == '' or blog_body == '':
            flash('Blog name and blog body required!', 'error')
            return render_template(
                'new_blog.html',
                title="Post a New Blog!",
                name=blog_name,
                body=blog_body)

        else:
            new_blog = Blog(blog_name, blog_body, owner)
            db.session.add(new_blog)
            db.session.commit()
            post_url = './post?id={0}'.format(new_blog.id)

            return redirect(post_url)

    return render_template(
        'new_blog.html', title="Post a New Blog!", name=' ', body=' ')


@app.route("/blog", methods=['GET'])
@app.route('/', methods=['GET'])
def blogs():

    blogs = Blog.query.all()
    blogs = list(reversed(blogs))

    return render_template(
        'all_blogs.html',
        title="Blogs!",
        blogs=blogs,
        endpoint='/blog')


@app.route("/myblog", methods=['GET'])
def myblogs():
    owner = User.query.filter_by(email=session['email']).first()

    blogs = Blog.query.filter_by(owner=owner).all()
    blogs = list(reversed(blogs))

    return render_template(
        'all_blogs.html', title="My Blog!", blogs=blogs, endpoint='/myblog')


@app.route("/users", methods=['GET'])
def users():
    users = User.query.all()
    return render_template(
        'all_users.html', title="All Users", users=users, endpoint='/users')


@app.route("/userblog", methods=['GET'])
def userblogs():
    id = request.args.get('id')
    owner = User.query.filter_by(id=id).first()

    blogs = Blog.query.filter_by(owner=owner).all()
    blogs = list(reversed(blogs))

    return render_template(
        'all_blogs.html',
        title="{0}'s' Blog!".format(owner.username),
        blogs=blogs,
        endpoint='/userblog',
        owner=owner)


@app.route("/post", methods=['GET'])
def single_post():
    id = request.args.get('id')
    blog = Blog.query.filter_by(id=id).first()

    return render_template('single_post.html', blog=blog, title=blog.name)


if __name__ == '__main__':
    app.run()
