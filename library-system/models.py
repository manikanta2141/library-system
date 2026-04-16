from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

# ---------------- USER ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), default='user')
    active = db.Column(db.Boolean, default=True)

    memberships = db.relationship('Membership', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)


# ---------------- MEMBERSHIP ----------------
class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    start_date = db.Column(db.Date, default=datetime.utcnow)
    end_date = db.Column(db.Date, nullable=False)

    active = db.Column(db.Boolean, default=True)


# ---------------- PRODUCT (NEW - REQUIRED) ----------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code_from = db.Column(db.String(20))
    code_to = db.Column(db.String(20))
    category = db.Column(db.String(100))


# ---------------- ITEM ----------------
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20))  # book/movie

    copies = db.relationship('ItemCopy', backref='item', lazy=True)


# ---------------- ITEM COPY ----------------
class ItemCopy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

    serial_no = db.Column(db.String(100), unique=True)
    available = db.Column(db.Boolean, default=True)

    transactions = db.relationship('Transaction', backref='copy', lazy=True)


# ---------------- TRANSACTION ----------------
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_copy_id = db.Column(db.Integer, db.ForeignKey('item_copy.id'), nullable=False)

    issue_date = db.Column(db.Date, default=datetime.utcnow)
    due_date = db.Column(db.Date, default=lambda: datetime.utcnow() + timedelta(days=15))
    return_date = db.Column(db.Date)

    status = db.Column(db.String(20), default='ISSUED')

    fine = db.Column(db.Float, default=0)
    fine_paid = db.Column(db.Boolean, default=False)