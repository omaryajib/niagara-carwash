import os

basedir = os.path.abspath(os.path.dirname(__file__))

config = {
    'SECRET_KEY': os.environ.get('SECRET_KEY') or 'super-secret-key',
    'DATABASE': os.path.join(basedir, '..', 'users.db')  # ⚠️ Change selon ton vrai nom de base
}
