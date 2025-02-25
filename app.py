from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User
import mysql.connector
import credentials
import os
import subprocess
import uuid

app = Flask(__name__)
db_config = credentials.dbconf
app.config['SECRET_KEY'] = '37THc0MDHugi7DMsHOxPEPShgD6RrjVFokIpHUwxQDq9gEcsr9u6i0CeKDf2iaba'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
shell_sessions = {}
DASHBOARDS_DIR = os.path.join(os.path.dirname(__file__), 'dashboards')
os.makedirs(DASHBOARDS_DIR, exist_ok=True)


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
def home():
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
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                cursor.close()
                conn.close()
            except mysql.connector.Error as err:
                flash(f'Error executing query: {err}', 'error')
    return render_template('reports.html', query=query, results=results, columns=columns)


@app.route('/workflows', methods=['GET', 'POST'])
def workflows():
    output = ""
    command = ""
    if request.method == 'POST':
        command = request.form.get('command', '').strip()
        if command:
            try:
                print(f"Executing command: {command}")
                if 'shell_id' not in session:
                    # Generate a unique session ID
                    session['shell_id'] = str(uuid.uuid4())
                    print(f"New shell session created with ID: {session['shell_id']}")
                shell_id = session['shell_id']
                if shell_id not in shell_sessions:
                    shell_sessions[shell_id] = subprocess.Popen(
                        ['/bin/bash'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        universal_newlines=True,
                        bufsize=1
                    )
                    print(f"New shell process created for session ID: {shell_id}")
                shell = shell_sessions[shell_id]
                shell.stdin.write(command + '\n')
                shell.stdin.flush()
                timeout = 5
                try:
                    stdout, stderr = shell.communicate(timeout=timeout)
                    output = stdout
                    if stderr:
                        output += f"\nError: {stderr}"
                except subprocess.TimeoutExpired:
                    shell.terminate()
                    output = "Command timed out."
                except Exception as err:
                    output = f"Error: {err}"
                print(f"Command output: {output}")
            except Exception as err:
                output = f"Error: {err}"
                print(f"Error executing command: {err}")
    return render_template('workflows.html', command=command, output=output)
@app.route('/workflows/reset', methods=['POST'])
def reset_workflows():
    # Reset the shell session
    if 'shell_id' in session:
        shell_id = session['shell_id']
        if shell_id in shell_sessions:
            shell_sessions[shell_id].terminate()
            del shell_sessions[shell_id]
        session.pop('shell_id')
    return redirect(url_for('workflows'))


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
                filepath = os.path.join(DASHBOARDS_DIR, filename)
                with open(filepath, 'w') as file:
                    file.write(content)
                flash(f'File "{filename}" created successfully!', 'success')
            except Exception as err:
                flash(f'Error creating file: {err}', 'error')
    files = [f for f in os.listdir(DASHBOARDS_DIR) if f.endswith('.html')]
    return render_template('dashboards.html', files=files)
@app.route('/dashboards/<filename>')
def view_dashboard(filename):
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
