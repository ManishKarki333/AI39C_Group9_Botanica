from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('index.html')

@auth_bp.route('/library')
def library():
    return render_template('library.html')

@auth_bp.route('/login')
def login():
    return render_template('login.html')

@auth_bp.route('/change-password')
def change_password():
    return render_template('change_password.html')
