from flask import Flask, render_template, request, redirect, session
from models import db, User, Item, ItemCopy, Transaction, Product
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "secret"

db.init_app(app)

# ---------------- INIT ----------------
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username='adm').first():
        db.session.add(User(username='adm', password=generate_password_hash('adm'), role='admin'))
        db.session.add(User(username='user', password=generate_password_hash('user'), role='user'))
        db.session.commit()


# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect('/admin' if user.role == 'admin' else '/user')

        return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')


# ---------------- ADMIN HOME ----------------
@app.route('/admin')
def admin_home():
    if session.get('role') != 'admin':
        return redirect('/')
    return render_template('admin_home.html')


# ---------------- USER HOME ----------------
@app.route('/user')
def user_home():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('user_home.html')


# ================= PRODUCT =================

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if session.get('role') != 'admin':
        return redirect('/')

    if request.method == 'POST':
        p = Product(
            code_from=request.form['code_from'],
            code_to=request.form['code_to'],
            category=request.form['category']
        )
        db.session.add(p)
        db.session.commit()
        return redirect('/view_products')

    return render_template('add_product.html')


@app.route('/view_products')
def view_products():
    if 'user_id' not in session:
        return redirect('/')

    products = Product.query.all()
    return render_template('view_products.html', products=products)


# ================= BOOK ADD =================

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if session.get('role') != 'admin':
        return redirect('/')

    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        serial = request.form.get('serial')

        if not title or not serial:
            return render_template('add_book.html', error="Title and Serial required")

        item = Item(name=title, type=category or 'book')
        db.session.add(item)
        db.session.commit()

        copy = ItemCopy(item_id=item.id, serial_no=serial, available=True)
        db.session.add(copy)
        db.session.commit()

        return redirect('/admin')

    return render_template('add_book.html')


# ================= CHECK BOOKS =================

@app.route('/check', methods=['GET', 'POST'])
def check_books():
    if 'user_id' not in session:
        return redirect('/')

    query = request.form.get('search')

    if query:
        items = Item.query.filter(Item.name.contains(query)).all()
    else:
        items = Item.query.all()

    return render_template('check_books.html', items=items)


# ================= ISSUE =================

@app.route('/issue', methods=['POST'])
def issue():
    if 'user_id' not in session:
        return redirect('/')

    item_id = request.form.get('item_id')

    if not item_id:
        return "Select a book"

    item = Item.query.get(item_id)

    if not item:
        return "Invalid item"

    copy = ItemCopy.query.filter_by(item_id=item.id, available=True).first()

    if not copy:
        return "No copies available"

    trans = Transaction(
        user_id=session['user_id'],
        item_copy_id=copy.id,
        status='ISSUED',
        due_date=datetime.utcnow() + timedelta(days=15)
    )

    copy.available = False
    db.session.add(trans)
    db.session.commit()

    return redirect('/check')


# ================= RETURN =================

@app.route('/return_page')
def return_page():
    if 'user_id' not in session:
        return redirect('/')

    transactions = Transaction.query.filter_by(
        user_id=session['user_id'], status='ISSUED'
    ).all()

    return render_template('return_book.html', transactions=transactions)


@app.route('/return', methods=['POST'])
def return_book():
    trans = Transaction.query.get(request.form['transaction_id'])

    if not trans:
        return "Invalid transaction"

    trans.return_date = datetime.utcnow()
    trans.status = 'RETURNED'

    if trans.return_date > trans.due_date:
        days = (trans.return_date - trans.due_date).days
        trans.fine = days * 10

    copy = ItemCopy.query.get(trans.item_copy_id)
    copy.available = True

    db.session.commit()

    return redirect(f"/payfine/{trans.id}")


# ================= PAY FINE =================

@app.route('/payfine/<int:id>', methods=['GET', 'POST'])
def payfine(id):
    trans = Transaction.query.get(id)

    if request.method == 'POST':
        if trans.fine > 0 and not request.form.get('paid'):
            return render_template('pay_fine.html', trans=trans, error="Pay fine first")

        trans.fine_paid = True
        db.session.commit()
        return redirect('/user')

    return render_template('pay_fine.html', trans=trans)


# ================= REPORTS =================

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect('/')

    active = Transaction.query.filter_by(status='ISSUED').all()

    overdue = Transaction.query.filter(
        Transaction.status == 'ISSUED',
        Transaction.due_date < datetime.utcnow()
    ).all()

    return render_template('reports.html', active=active, overdue=overdue)


# ================= LOGOUT =================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)