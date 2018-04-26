from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:asdf@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'U6JtITN8Qc'


class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120)) 
    body = db.Column(db.String(1000))
    blog_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        blog_date = datetime.utcnow()
        self.blog_date = blog_date
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    email = ''
    password = ''
    email_error = ''
    password_error = ''

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['email'] = email
            return redirect('/newpost')
        elif user:
            if user.password != password:
                password_error = 'Incorrect Password'
                password = ''
                return render_template('login.html', email=email,
                    password=password,
                    email_error=email_error,
                    password_error=password_error)
        elif not user:
            email_error = 'email does not exist'
            return render_template('login.html', email=email,
                    password=password,
                    email_error=email_error,
                    password_error=password_error)
    else:
        return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        email_error = ''
        password_error = ''
        verify_error = ''

        if len(email) < 3 or len(email) > 20 or ' ' in email or '@' not in email or '.' not in email:
            email_error = "That's not a valid email"
        
        if len(password) < 3 or len(password) > 20 or ' 'in password:
            password_error = "That's not a valid password"

        if verify != password:
            verify_error = "Passwords don't match"
            verify = ''
        
        if password_error:
            password = ''

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            email_error = 'Sorry, we already have a user under that email.'

        if email_error or password_error or verify_error:
            return render_template('signup.html',
                email=email,
                email_error=email_error,
                password=password,
                password_error=password_error,
                verify=verify,
                verify_error=verify_error)

        
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/blog')

    return render_template('signup.html')

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if 'email' not in session:
        return redirect('/blog')
    else:
        del session['email']
        return redirect('/blog')

@app.route('/')
def index():
    users = User.query.order_by(User.email).all()
    return render_template('index.html', users=users)

@app.route('/blog')
def blog():
    if (request.args.get('id')):
        id = request.args.get('id')
        blog = Blog.query.filter_by(id=id).first()
        owner_id = blog.owner_id
        title = blog.title
        body = blog.body
        users = User.query.filter_by(id=owner_id)
        return render_template('viewpost.html', users=users, title=title, body=body)

    elif (request.args.get('user')):
        userId = request.args.get('user')
        users = User.query.filter_by(id=userId)
        blogs = Blog.query.filter_by(owner_id=userId).order_by(Blog.blog_date.desc()).all()
        return render_template('viewuser.html', users=users, blogs=blogs)
    else:
        users = User.query.order_by(User.email).all()
        blogs = Blog.query.order_by(Blog.blog_date.desc()).all()
        return render_template('blog.html', users=users, blogs=blogs)

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    if request.method == 'POST':
        owner = User.query.filter_by(email=session['email']).first()
        title = request.form['title']
        body_name = request.form['body']
        
        #TODO - Make owner variable and add to 'newpost.html.'

        title_error = ''
        body_error = ''

        if title == '':
            title_error = 'Please fill in the title'

        if body_name == '':
            body_error = 'Please fill in the body'

        if title_error == '' and body_error == '':
            new_blog = Blog(title, body_name, owner)
            db.session.add(new_blog)
            db.session.commit()
            id = str(new_blog.id)
            return redirect('/blog?id=' + id)

        else:
            return render_template('newpost.html', title_error=title_error, body_error=body_error)

    else:
        return render_template('newpost.html')


if __name__ == '__main__':
    app.run()