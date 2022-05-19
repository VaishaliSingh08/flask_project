from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    user_id_pk = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False)
    user_email = db.Column(db.String(50), nullable=False)
    user_qualification = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), unique=False, nullable=False)
    cnfrm_pass = db.Column(db.String(50), unique=False, nullable=False)
    user_contact = db.Column(db.String(10), unique=False, nullable=False)
    is_active = db.Column(db.String(5), unique=False, nullable=False)
    user_image = db.Column(db.String(100), unique=False, nullable=False)

    db.create_all()

