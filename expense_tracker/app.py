from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "expense_tracker_secret_2026"

# 🔹 MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="expense_tracker"
)

# 🔹 Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# ================= HOME =================
@app.route('/')
def home():
    return redirect('/login')


# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        db.commit()

        flash("Registration Successful! Please login.")
        return redirect('/login')

    return render_template('register.html')


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            flash("Login Successful!")
            return redirect('/dashboard')
        else:
            flash("Invalid Credentials!")

    return render_template('login.html')


# ================= DASHBOARD =================
@app.route('/dashboard')
@login_required
def dashboard():
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM transactions WHERE user_id=%s",
        (session['user_id'],)
    )
    transactions = cursor.fetchall()

    # Total Income
    cursor.execute(
        "SELECT SUM(amount) AS total FROM transactions WHERE user_id=%s AND type='income'",
        (session['user_id'],)
    )
    income_data = cursor.fetchone()
    income = income_data['total'] if income_data['total'] else 0

    # Total Expense
    cursor.execute(
        "SELECT SUM(amount) AS total FROM transactions WHERE user_id=%s AND type='expense'",
        (session['user_id'],)
    )
    expense_data = cursor.fetchone()
    expense = expense_data['total'] if expense_data['total'] else 0

    balance = income - expense

    return render_template(
        'dashboard.html',
        transactions=transactions,
        income=income,
        expense=expense,
        balance=balance
    )

#-----------------EDIT---------------------

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    cursor = db.cursor(dictionary=True)

    # GET request → form show karega
    if request.method == 'GET':
        cursor.execute(
            "SELECT * FROM transactions WHERE id=%s AND user_id=%s",
            (id, session['user_id'])
        )
        transaction = cursor.fetchone()
        return render_template('edit.html', t=transaction)

    # POST request → update karega
    if request.method == 'POST':
        type = request.form['type']
        category = request.form['category']
        amount = request.form['amount']
        date = request.form['date']
        description = request.form['description']

        cursor.execute(
            """UPDATE transactions 
               SET type=%s, category=%s, amount=%s, date=%s, description=%s
               WHERE id=%s AND user_id=%s""",
            (type, category, amount, date, description, id, session['user_id'])
        )
        db.commit()

        flash("Transaction Updated Successfully!")
        return redirect('/dashboard')

#------------------DELETE----------------------

@app.route('/delete/<int:id>')
@login_required
def delete_transaction(id):
    cursor = db.cursor()

    # Security: sirf apni transaction delete kar sake
    cursor.execute(
        "DELETE FROM transactions WHERE id=%s AND user_id=%s",
        (id, session['user_id'])
    )

    db.commit()
    flash("Transaction Deleted Successfully!")
    return redirect('/dashboard')

# ================= ADD TRANSACTION =================
@app.route('/add', methods=['POST'])
@login_required
def add_transaction():
    type = request.form['type']
    category = request.form['category']
    amount = request.form['amount']
    description = request.form['description']
    date = request.form['date']

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, type, category, amount, description, date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (session['user_id'], type, category, amount, description, date))

    db.commit()
    flash("Transaction Added Successfully!")
    return redirect('/dashboard')


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)