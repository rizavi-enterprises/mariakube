from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User
import mysql.connector
import credentials
import os

app = Flask(__name__)
db_config = credentials.dbconf
app.config['SECRET_KEY'] = '37THc0MDHugi7DMsHOxPEPShgD6RrjVFokIpHUwxQDq9gEcsr9u6i0CeKDf2iaba'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/home')
@login_required
def dashboard():
    return render_template('home.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/reports', methods=['GET', 'POST'])
def reports():
    results = None
    query = ""
    columns = []

    if request.method == 'POST':
        query = request.form.get('query', '').strip()

        if query:
            try:
                # Connect to the database
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()

                # Execute the query
                cursor.execute(query)
                results = cursor.fetchall()

                # Get column names
                columns = [col[0] for col in cursor.description]

                cursor.close()
                conn.close()

            except mysql.connector.Error as err:
                flash(f'Error executing query: {err}', 'error')

    return render_template('reports.html', query=query, results=results, columns=columns)

@app.route('/workflows', methods=['GET', 'POST'])
def terminal():
    output = ""
    command = ""

    if request.method == 'POST':
        command = request.form.get('command', '').strip()

        if command:
            try:
                # Run the command in the terminal
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                output = result.stdout or result.stderr
            except Exception as err:
                output = f"Error: {err}"

    return render_template('terminal.html', command=command, output=output)

DASHBOARDS_DIR = os.path.join(os.path.dirname(__file__), 'dashboards')
os.makedirs(DASHBOARDS_DIR, exist_ok=True)  # Create directory if it doesn't exist

@app.route('/dashboards', methods=['GET', 'POST'])
def dashboards():
    if request.method == 'POST':
        # Handle file creation
        filename = request.form.get('filename', '').strip()
        content = request.form.get('content', '').strip()

        if not filename:
            flash('Filename is required.', 'error')
        elif not filename.endswith('.html'):
            flash('Filename must end with .html.', 'error')
        else:
            try:
                # Save the new HTML file
                filepath = os.path.join(DASHBOARDS_DIR, filename)
                with open(filepath, 'w') as file:
                    file.write(content)
                flash(f'File "{filename}" created successfully!', 'success')
            except Exception as err:
                flash(f'Error creating file: {err}', 'error')

    # List all HTML files in the directory
    files = [f for f in os.listdir(DASHBOARDS_DIR) if f.endswith('.html')]
    return render_template('dashboards.html', files=files)

@app.route('/dashboards/<filename>')
def view_dashboard(filename):
    # Serve the requested HTML file
    filepath = os.path.join(DASHBOARDS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            return file.read()
    else:
        flash(f'File "{filename}" not found.', 'error')
        return redirect(url_for('dashboards'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host=credentials.h, port=credentials.p)
