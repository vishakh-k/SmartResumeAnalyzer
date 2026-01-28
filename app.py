from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

# Initialize App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' # Switch to MySQL URI for production
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max

# Ensure upload dir exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    resumes = db.relationship('Resume', backref='author', lazy=True)
    
class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Linked to User
    
    # Parsed Data
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    mobile_number = db.Column(db.String(20))
    skills = db.Column(db.Text) # JSON string
    total_experience = db.Column(db.Float) # Years
    
    # Analytics
    predicted_role = db.Column(db.String(100))
    resume_score = db.Column(db.Integer)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# --- NLP ENGINE IMPORT ---
from nlp_engine import ResumeParser
parser = ResumeParser()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You can now log in', 'success')
            return redirect(url_for('login'))
        except:
            flash('Username or Email already exists.', 'danger')
            return redirect(url_for('register'))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('user_dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    if 'resume' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['resume']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parse Resume
        data = parser.parse(filepath)
        
        # Save to DB
        resume_entry = Resume(
            filename=filename,
            name=data['name'],
            email=data['email'],
            mobile_number=data['mobile_number'],
            skills=json.dumps(data['skills']),
            total_experience=data['total_experience'],
            predicted_role=data['predicted_role'],
            resume_score=data['resume_score'],
            author=current_user # Link to current user
        )
        db.session.add(resume_entry)
        db.session.commit()
        
        return render_template('user_dashboard.html', results=data, show_results=True)
        
    else:
        flash('Invalid file type. Please upload PDF.')
        return redirect(url_for('user_dashboard'))

@app.route('/feedback', methods=['POST'])
@login_required
def feedback():
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    fb = Feedback(rating=int(rating), comment=comment)
    db.session.add(fb)
    db.session.commit()
    
    return redirect(url_for('user_dashboard'))

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    # Simple check for robust admin auth later
    # if current_user.email != 'admin@example.com':
    #     return redirect(url_for('home'))

    # Fetch Analytics
    total_users = User.query.count() 
    resumes = Resume.query.all()
    avg_score = 0
    if resumes:
        avg_score = sum([r.resume_score for r in resumes]) // len(resumes)
    
    # Pie Chart Data (Role Distribution)
    roles = {}
    for r in resumes:
        role = r.predicted_role or "Unknown"
        roles[role] = roles.get(role, 0) + 1
        
    # Rating Distribution
    feedbacks = Feedback.query.all()
    ratings = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for f in feedbacks:
        if f.rating in ratings:
            ratings[f.rating] += 1
            
    return render_template('admin_dashboard.html', 
                           total_users=total_users, 
                           avg_score=avg_score,
                           role_distribution=roles,
                           rating_distribution=ratings,
                           resumes=resumes)

@app.route('/download_csv')
@login_required
def download_csv():
    import csv
    import io
    from flask import make_response
    
    resumes = Resume.query.all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Name', 'Email', 'Mobile', 'Role', 'Score', 'Filename', 'Date'])
    
    for r in resumes:
        cw.writerow([r.id, r.name, r.email, r.mobile_number, r.predicted_role, r.resume_score, r.filename, r.upload_date])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=applicants_data.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
