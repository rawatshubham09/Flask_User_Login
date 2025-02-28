import os
from flask import Flask, render_template, url_for, redirect, request, session, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
IMG_FOLDER = os.path.join("static", "images")
app.config["UPLOAD_FOLDER"] = IMG_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = 'your_secret_key' # Add a secret key for session management
db = SQLAlchemy(app)
ARTIFACTS_DIR = "artifacts"
IMAGE_FOLDER = os.path.join('static', 'images')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))] # only get images.
    return render_template('index.html', images=images, enumerate=enumerate)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        print("{name}: {email}: {password}")

        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")

        new_user = User(name=name, email=email, password=password)

        db.session.add(new_user)
        db.session.commit()

        # Explicitly modify and save the session
        session["name"] = new_user.name
        session["email"] = new_user.email
        session.modified = True  # Mark the session as modified

        return redirect(url_for("dashboard"))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            print("Password check successful") #add this line
            session["name"] = user.name
            session["email"] = user.email
            return redirect(url_for("dashboard"))
        else:
            print("Password check failed") #add this line
            return render_template('login.html', error="Invalid User")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop("name", None)
    session.pop("email", None)
    return redirect(url_for("login"))

@app.route('/dashboard')
def dashboard():
    if "name" in session:
        folders = [f for f in os.listdir(ARTIFACTS_DIR) if os.path.isdir(os.path.join(ARTIFACTS_DIR, f))]
        return render_template("dashboard.html", name=session["name"], folders=folders)
    return redirect(url_for("login"))

@app.route('/logs')
def display_logs():
    if "name" in session:
        log_path = 'logs.txt'
        with open(log_path, 'r') as file:
            log_content = file.read()
        return render_template('logs.html', log_content=log_content)
    return redirect(url_for("login"))

def create_artifact_routes():
    if not os.path.exists(ARTIFACTS_DIR):
        return

    for folder_name in os.listdir(ARTIFACTS_DIR):
        folder_path = os.path.join(ARTIFACTS_DIR, folder_name)
        if os.path.isdir(folder_path):
            # Generate unique endpoint names
            download_endpoint = f'download_{folder_name}'
            list_endpoint = f'list_{folder_name}'

            @app.route(f'/{folder_name}/<filename>', endpoint=download_endpoint)
            def artifact_download(filename, folder_name=folder_name):
                artifact_path = os.path.join(ARTIFACTS_DIR, folder_name, filename)
                if os.path.isfile(artifact_path):
                    return send_from_directory(os.path.join(ARTIFACTS_DIR, folder_name), filename, as_attachment=True)
                else:
                    abort(404)

            @app.route(f'/{folder_name}', endpoint=list_endpoint)
            def artifact_list(folder_name=folder_name):
                artifact_folder_path = os.path.join(ARTIFACTS_DIR, folder_name)
                files = [f for f in os.listdir(artifact_folder_path) if os.path.isfile(os.path.join(artifact_folder_path, f))]
                return render_template("artifact_list.html", folder_name=folder_name, files=files)

create_artifact_routes()

@app.route('/train')
def train():
    if "name" in session:
        return render_template('train.html', )
    return redirect(url_for("login"))

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory("artifacts", filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)