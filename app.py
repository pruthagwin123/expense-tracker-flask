from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from config import Config
from models import init_db, create_user, get_user_by_email, get_user_by_id, add_category, get_categories, add_expense, get_expenses, summary_by_category, export_expenses_csv
from reporting import generate_monthly_report
from mail_utils import init_mail, send_summary_email
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import io
import datetime
import csv

app = Flask(__name__)
app.config.from_object(Config)
bcrypt = Bcrypt(app)

# init DB, mail
init_db(app)
init_mail(app := app)  # note: mail init needs app configured

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Simple User class for flask-login


class User(UserMixin):
    def __init__(self, userdict):
        self.id = userdict['id']
        self.username = userdict['username']
        self.email = userdict['email']


@login_manager.user_loader
def load_user(user_id):
    u = get_user_by_id(user_id)
    if u:
        return User(u)
    return None


@app.route('/')
def idx():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Register


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        if get_user_by_email(email):
            flash("Email already exists", "danger")
            return redirect(url_for('register'))
        pw_hash = bcrypt.generate_password_hash(password).decode()
        create_user(username, email, pw_hash)
        flash("Registered. Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# Login


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        ud = get_user_by_email(email)
        if ud and bcrypt.check_password_hash(ud['password'], password):
            user = User(ud)
            login_user(user)
            flash("Logged in", "success")
            return redirect(url_for('dashboard'))
        flash("Invalid credentials", "danger")
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for('login'))

# Dashboard


@app.route('/dashboard')
@login_required
def dashboard():
    # Allow user to pick a month & year, default to current month
    today = datetime.date.today()
    selected_year = int(request.args.get('year', today.year))
    selected_month = int(request.args.get('month', today.month))

    # Calculate start and end dates for the selected month
    start = datetime.date(selected_year, selected_month, 1)
    if selected_month == 12:
        end = datetime.date(selected_year + 1, 1, 1) - \
            datetime.timedelta(days=1)
    else:
        end = datetime.date(selected_year, selected_month +
                            1, 1) - datetime.timedelta(days=1)

    # Fetch data
    expenses = get_expenses(
        current_user.id, start.isoformat(), end.isoformat())
    categories = get_categories(current_user.id)
    cat_summary = summary_by_category(
        current_user.id, start.isoformat(), end.isoformat())
    labels = [r[0] for r in cat_summary]
    values = [float(r[1] or 0) for r in cat_summary]

    # Prepare dropdown options for month/year
    # last 3 years + current
    years = list(range(today.year - 3, today.year + 1))
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    return render_template(
        'dashboard.html',
        expenses=expenses,
        categories=categories,
        labels=labels,
        values=values,
        start=start,
        end=end,
        selected_month=selected_month,
        selected_year=selected_year,
        months=months,
        years=years
    )


# Add category


@app.route('/category/add', methods=['POST'])
@login_required
def category_add():
    name = request.form['category_name']
    if name:
        add_category(current_user.id, name)
    return redirect(url_for('dashboard'))

# Add expense


@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def expense_add():
    if request.method == 'POST':
        category_id = request.form.get('category_id') or None
        amount = float(request.form['amount'])
        description = request.form.get('description', '')
        date_str = request.form.get(
            'date') or datetime.date.today().isoformat()
        recurring = request.form.get('recurring') or None
        add_expense(current_user.id, category_id, amount,
                    description, date_str, recurring)
        flash("Expense added", "success")
        return redirect(url_for('dashboard'))
    categories = get_categories(current_user.id)
    return render_template('add_expense.html', categories=categories)

# Export CSV


@app.route('/export/csv')
@login_required
def export_csv():
    # Get selected month & year
    month = request.args.get("month", datetime.date.today().month, type=int)
    year = request.args.get("year", datetime.date.today().year, type=int)

    # Calculate date range
    start = datetime.date(year, month, 1)
    if month == 12:
        end = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

    # Now fetch CSV only for that range
    csv_data = export_expenses_csv(
        current_user.id, start.isoformat(), end.isoformat())

    return send_file(
        io.BytesIO(csv_data.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'expenses_{year}-{month:02d}.csv'
    )


# Generate PDF for month


@app.route('/report_pdf')
@login_required
def report_pdf():
    # Get selected month & year from query parameters
    month = request.args.get("month", datetime.datetime.now().month, type=int)
    year = request.args.get("year", datetime.datetime.now().year, type=int)

    # Compute date range
    start = datetime.date(year, month, 1)
    if month == 12:
        end = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

    # Get expenses for current user in the selected range
    expenses = get_expenses(
        current_user.id, start.isoformat(), end.isoformat())

    if not expenses:
        flash("No expenses found for the selected period.", "warning")
        return redirect(url_for("dashboard"))

    # Generate PDF bytes (using your reporting.py function)
    pdf_bytes = generate_monthly_report(get_user_by_id(
        current_user.id), expenses, f"{year}-{month:02d}")

    # Send the file as a download
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"report_{year}-{month:02d}.pdf"
    )


# Send monthly email summary (example)
@app.route('/email/monthly')
@login_required
def email_monthly():
    # Get month & year from dashboard filters
    month = request.args.get("month", datetime.date.today().month, type=int)
    year = request.args.get("year", datetime.date.today().year, type=int)

    # Compute date range for the selected month
    start = datetime.date(year, month, 1)
    if month == 12:
        end = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

    # Fetch filtered data
    expenses = get_expenses(
        current_user.id, start.isoformat(), end.isoformat())
    if not expenses:
        flash("No expenses found for the selected month.", "warning")
        return redirect(url_for('dashboard'))

    total = sum(float(e['amount']) for e in expenses)

    # Prepare email
    month_name = start.strftime("%B %Y")
    body = f"Expense summary for {month_name}\nTotal Spent: ₹{total:.2f}\n\nAttached is your monthly PDF report."
    pdf_bytes = generate_monthly_report(
        get_user_by_id(current_user.id), expenses, month_name)

    # Send email with attached PDF
    send_summary_email(
        current_user.email,
        f"Expense Summary - {month_name}",
        body,
        attachments=[(f"report_{month_name}.pdf",
                      pdf_bytes, "application/pdf")]
    )

    flash(f"Email with {month_name} summary sent successfully!", "success")
    return redirect(url_for('dashboard'))


# Chart data API


@app.route('/api/chart-data')
@login_required
def chart_data():
    start = request.args.get('start')
    end = request.args.get('end')
    rows = summary_by_category(current_user.id, start, end)
    labels = [r[0] for r in rows]
    values = [float(r[1] or 0) for r in rows]
    return jsonify({'labels': labels, 'values': values})


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

