from flask import Flask, render_template, request, url_for, session, redirect
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer as Serializer, SignatureExpired
from flask_mail import Mail, Message
import hashlib
import smtplib
import os

from werkzeug.utils import secure_filename

from flask_session import Session

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

s = Serializer('cbfwufbuefbqeufbqefbq')

uploads_dir = os.path.join('static/uploads')
os.makedirs(uploads_dir, exist_ok=True)

app.config.update(MAIL_SERVER='smtp.gmail.com',
                  MAIL_PORT=465,
                  MAIL_USE_SSL = True,
                  MAIL_USE_TLS = False,
                  MAIL_USERNAME='vaishaliofficial08@gmail.com',
                  MAIL_PASSWORD='zynga123!@#')

mail = Mail(app)

# conn = psycopg2.connect(dbname="postgres", user="postgres", password="zynga", host="localhost", port ="5432")
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:zynga@localhost/flask'

db = SQLAlchemy(app)
app.debug = True


class User(db.Model):
    user_id_pk = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False)
    user_email = db.Column(db.String(50), nullable=False)
    user_qualification = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), unique=False, nullable=False)
    cnfrm_pass = db.Column(db.String(50), unique=False, nullable=False)
    user_contact = db.Column(db.String(10), unique=False, nullable=False)
    is_active = db.Column(db.String(5), unique=False, nullable=True)
    user_image = db.Column(db.String(100), unique=False, nullable=True)
    token = db.Column(db.String(50), unique=False, nullable=True)

    def __init__(self, user_name, user_email, user_qualification, password, cnfrm_pass, user_contact, is_active,
                 user_image, token):
        self.user_name = user_name
        self.user_email = user_email
        self.user_qualification = user_qualification
        self.password = password
        self.cnfrm_pass = cnfrm_pass
        self.user_contact = user_contact
        self.is_active = is_active
        self.user_image = user_image
        self.token = token


class Prod(db.Model):
    p_id_pk = db.Column(db.Integer, primary_key=True)
    p_name = db.Column(db.String(50), nullable=False)
    p_desc = db.Column(db.String(200), unique=False, nullable=False)
    p_price = db.Column(db.String(10), unique=False, nullable=True)
    p_image = db.Column(db.String(100), unique=False, nullable=True)
    user_id_fk = db.Column(db.Integer)

    def __init__(self, p_name, p_desc, p_price, p_image, user_id_fk):
        self.p_name = p_name
        self.p_desc = p_desc
        self.p_price = p_price
        self.p_image = p_image
        self.user_id_fk = user_id_fk


@app.route('/')
def home():
    return render_template("pillowmart/index.html")


@app.route('/register', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        user_name = request.form['user_name']
        user_contact = request.form['contact']
        user_email = request.form['email']
        user_qualification = request.form['qualification']
        password_one = request.form['password_one']
        password_two = request.form['password_two']
        user_image = request.files['image']
        error_msg = ''
        user_image.save(os.path.join(uploads_dir, secure_filename(user_image.filename)))
        url = user_image.filename

        if db.session.query(db.exists().where(User.user_email == user_email)).scalar():
            error_msg = 'Email is already in use !!'

        if db.session.query(db.exists().where(User.user_name == user_name)).scalar():
            error_msg = 'Username taken !!'


        success = "Please check mail to confirm your account !!"
        if error_msg == '':
            token = s.dumps(user_email, salt='email-confirm')
            print(token)
            msg = Message('Confirm Email',
                          sender='vaishali.singh.ms@gmail.com',
                          recipients=[user_email])
            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Please confirm your registration using this link {}'.format(link)
            mail.send(msg)


            new_user = User(is_active='False', user_contact=user_contact,
                            user_name=user_name, user_email=user_email, user_qualification=user_qualification,
                            password=password_one,cnfrm_pass=password_two, user_image = url, token = token)
            db.session.add(new_user)
            db.session.commit()
            return render_template("pillowmart/sign_up.html", error_msg=error_msg, user_name=user_name,
                                   user_email=user_email, user_contact=user_contact,
                                   user_qualification=user_qualification, success = success)
        else:
            return render_template("pillowmart/sign_up.html", error_msg=error_msg, user_name=user_name,
                                   user_email=user_email, user_contact=user_contact,
                                   user_qualification=user_qualification)



    else:
        return render_template("pillowmart/sign_up.html")


@app.route('/confirm_email/<token>')
def confirm_email(token):
    email = s.loads(token, salt='email-confirm', max_age=1800)
    update = User.query.filter_by(user_email=email).first()
    update.is_active = True
    db.session.commit()


    return render_template('pillowmart/confirmation.html')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(email, password)
        error_msg = ''
        if check_user_exist(email, password):
            session['user_email'] = email
            # id = User.query.filter_by(user_email=email).all()

            id = db.session.query(User.user_email, User.user_id_pk).all()
            a = id[0]
            (user_email, user_id) = a
            session['user_id_pk'] = user_id
            user = User.query.filter_by(user_email=email).first()
            print(user.is_active)
            if user.is_active == "true":
                return redirect('/dashboard')
            else:
                error_msg = "Your account is not yet confirmed. Please check your mail and confirm your account!"
                return render_template('pillowmart/login.html', error_msg=error_msg)
        else:
            error_msg = "Credentials are not valid !!"
            return render_template('pillowmart/login.html', error_msg=error_msg)
    return render_template('pillowmart/login.html')



@app.route("/logout")
def logout():
    session.pop('user_email', None)
    session.pop('user_id', None)

    return redirect('/shop_products')


@app.route("/user_profile", methods=['POST', 'GET'])
def user_profile():
    email = session['user_email']
    user = User.query.filter_by(user_email=email).first()
    user_name = user.user_name
    user_contact = user.user_contact
    user_email = user.user_email
    user_qualification = user.user_qualification
    password_one = user.password
    user_image = user.user_image

    if request.method == 'POST':
        user_name = request.form['user_name']
        user_contact = request.form['contact']
        user_email = request.form['email']
        user_qualification = request.form['qualification']
        password_one = request.form['password_one']
        update = User.query.filter_by(user_email=email).first()
        user.user_name = user_name
        user.user_contact = user_contact
        user.user_email = user_email
        user.user_qualification = user_qualification
        user.password = password_one
        db.session.commit()

        if request.files['image']:
            user_image = request.files['image']
            user_image.save(os.path.join(uploads_dir, secure_filename(user_image.filename)))
            url =user_image.filename
            print(url)
            update = User.query.filter_by(user_email=email).first()
            update.user_image = url
            return render_template('dashboard/user_profile.html', user_name=user_name, user_email=user_email,
                               user_qualification=user_qualification, user_contact=user_contact, password=password_one, user_image = url)

    return render_template('dashboard/user_profile.html', user_name=user_name, user_email=user_email,
                           user_qualification=user_qualification, user_contact=user_contact, password=password_one, user_image= user_image)


@app.route('/dashboard')
def dashboard():
    email = session['user_email']
    user = User.query.filter_by(user_email=email).first()
    user_name = user.user_name
    user_image = user.user_image
    return render_template('dashboard/index.html', user_name = user_name, user_image = user_image)


@app.route('/shop_products')
def shop_products():
    prod = Prod.query.all()


    return render_template('pillowmart/product_list.html', prod = prod)


@app.route('/add_products', methods=['POST','GET'])
def add_products():
    email = session['user_email']
    user = User.query.filter_by(user_email=email).first()
    user_name = user.user_name
    user_image = user.user_image
    user_id = user.user_id_pk

    if request.method == 'POST':
        p_name = request.form['p_name']
        p_desc = request.form['p_desc']
        p_price = request.form['p_price']
        p_image = request.files['p_image']

        p_image.save(os.path.join(uploads_dir, secure_filename(p_image.filename)))
        url = p_image.filename

        new_product = Prod(p_name=p_name, p_desc=p_desc, p_price=p_price, p_image=url, user_id_fk=user_id)
        db.session.add(new_product)
        db.session.commit()
        return redirect('/products')
    else:
        return render_template('dashboard/add_product.html', user_image = user_image, user_name = user_name)

@app.route('/edit_products/<int:id>', methods=['GET', 'POST'])
def edit_products(id):
    email = session['user_email']
    user = User.query.filter_by(user_email=email).first()
    user_name = user.user_name
    user_id = user.user_id_pk
    user_image = user.user_image
    prod = Prod.query.filter_by(p_id_pk=str(id)).first()
    img = prod.p_image
    if request.method == 'POST':
        p_name = request.form['p_name']
        p_desc = request.form['p_desc']
        p_price = request.form['p_price']
        update = Prod.query.filter_by(user_id_fk=str(id)).first()
        prod.p_name = p_name
        prod.p_desc = p_desc
        prod.p_price = p_price
        update = Prod.query.filter_by(user_id_fk=str(id)).first()
        prod.p_name = p_name
        prod.p_desc = p_desc
        prod.p_price = p_price
        db.session.commit()

        if request.files['p_image']:
            p_image = request.files['p_image']
            p_image.save(os.path.join(uploads_dir, secure_filename(p_image.filename)))
            url = p_image.filename
            print(url)
            update = Prod.query.filter_by(p_id_pk=str(id)).first()

            update.p_image = url
            db.session.commit()
            print('path',url)
            return redirect('/products')

        return redirect('/products')

    return render_template("dashboard/edit_product.html", prod=prod, user_name=user_name, user_image=user_image)



@app.route('/delete_prod/<int:id>')
def delete_prod(id):
    Prod.query.filter_by(p_id_pk=str(id)).delete()
    db.session.commit()
    # User.query.filter_by(id=123).delete()
    return  redirect('/products')


@app.route('/products')
def products():
    email = session['user_email']
    user = User.query.filter_by(user_email=email).first()
    user_name = user.user_name
    user_id = user.user_id_pk
    user_image = user.user_image
    message = ''
    if db.session.query(Prod).filter(Prod.user_id_fk == str(user_id)):
        product = Prod.query.filter_by(user_id_fk=str(user_id)).all()
        return render_template('dashboard/product_list.html', user_name=user_name, product = product, user_image= user_image)

    else:
        message = "Success"
        return render_template('dashboard/product_list.html',message = message, user_image= user_image, user_name  = user_name)










def check_user_exist(email, password):
    object_values = User.query.filter_by(user_email=email, password=password).first()
    return object_values


def get_id(email):
    object_values = User.query.filter_by(user_email=email)

    return object_values


def get_all_object_from_id(id):
    object_values = User.query.get(id)
    return object_values


if __name__ == '__main__':
    app.run(debug=True)
