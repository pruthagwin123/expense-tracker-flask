import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change_this_to_secret')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'your_mysql_password')
    MYSQL_DB = os.getenv('MYSQL_DB', 'expense_tracker')

    # Flask-Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')  # your email
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # email password or app password
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
