from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import date
import pandas as pd
import io
import csv

mysql = None


def init_db(app):
    global mysql
    mysql = MySQL(app)

# Users


def create_user(username, email, password_hash):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("INSERT INTO users (username, email, password) VALUES (%s,%s,%s)",
                (username, email, password_hash))
    mysql.connection.commit()
    cur.close()


def get_user_by_email(email):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    return user


def get_user_by_id(user_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return user

# Categories


def get_categories(user_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM categories WHERE user_id=%s", (user_id,))
    rows = cur.fetchall()
    cur.close()
    return rows


def add_category(user_id, name):
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO categories (user_id, name) VALUES (%s,%s)", (user_id, name))
    mysql.connection.commit()
    cur.close()

# Expenses


def add_expense(user_id, category_id, amount, description, date_str, recurring_rule=None):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO expenses (user_id, category_id, amount, description, date, recurring_rule) VALUES (%s,%s,%s,%s,%s,%s)",
                (user_id, category_id, amount, description, date_str, recurring_rule))
    mysql.connection.commit()
    cur.close()


def get_expenses(user_id, start_date=None, end_date=None):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    q = "SELECT e.*, c.name as category FROM expenses e LEFT JOIN categories c ON e.category_id=c.id WHERE e.user_id=%s"
    params = [user_id]
    if start_date:
        q += " AND date >= %s"
        params.append(start_date)
    if end_date:
        q += " AND date <= %s"
        params.append(end_date)
    q += " ORDER BY date DESC"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    return rows


def summary_by_category(user_id, start_date=None, end_date=None):
    cur = mysql.connection.cursor()
    q = "SELECT c.name, SUM(e.amount) FROM expenses e LEFT JOIN categories c ON e.category_id=c.id WHERE e.user_id=%s"
    params = [user_id]
    if start_date:
        q += " AND date >= %s"
        params.append(start_date)
    if end_date:
        q += " AND date <= %s"
        params.append(end_date)
    q += " GROUP BY c.name"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    return rows


def export_expenses_csv(user_id, start_date, end_date):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = """
        SELECT e.id, e.user_id, e.category_id, e.amount, e.description, e.date, e.recurring_rule AS recurring, c.name AS category
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s AND e.date BETWEEN %s AND %s
        ORDER BY e.date DESC
    """
    cur.execute(query, (user_id, start_date, end_date))
    rows = cur.fetchall()
    cur.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'user_id', 'category_id', 'amount',
                    'description', 'date', 'recurring', 'category'])
    for row in rows:
        writer.writerow([
            row['id'], row['user_id'], row['category_id'], row['amount'],
            row['description'], row['date'], row['recurring'], row['category']
        ])

    return output.getvalue()
