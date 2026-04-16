from datetime import datetime, timedelta
from models import db, Transaction, ItemCopy, Membership

FINE_PER_DAY = 5

def issue_book(user_id, item_copy_id):
    copy = ItemCopy.query.get(item_copy_id)

    if not copy or not copy.available:
        return "Book not available"

    membership = Membership.query.filter_by(user_id=user_id, active=True).first()

    if not membership or membership.end_date < datetime.utcnow().date():
        return "Membership expired"

    due_date = datetime.utcnow().date() + timedelta(days=15)

    transaction = Transaction(
        user_id=user_id,
        item_copy_id=item_copy_id,
        due_date=due_date
    )

    copy.available = False

    db.session.add(transaction)
    db.session.commit()

    return "Book issued"


def return_book(transaction_id):
    transaction = Transaction.query.get(transaction_id)

    if not transaction or transaction.status == 'RETURNED':
        return "Invalid transaction"

    today = datetime.utcnow().date()

    transaction.return_date = today
    transaction.status = 'RETURNED'

    # Fine calculation
    if today > transaction.due_date:
        days = (today - transaction.due_date).days
        transaction.fine = days * FINE_PER_DAY

    copy = ItemCopy.query.get(transaction.item_copy_id)
    copy.available = True

    db.session.commit()

    return transaction.fine