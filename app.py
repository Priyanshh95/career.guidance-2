from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///career_guidance.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    assessments = db.relationship('Assessment', backref='user', lazy=True)

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)

class Career(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    salary_range = db.Column(db.String(100))
    growth_potential = db.Column(db.String(50))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')  # <-- Possible issue: username may be None
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('signup'))
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/job_recommendation', methods=['GET', 'POST'])
def job_recommendation():
    engineering_subjects = [
        "Computer Science", "Mechanical Engineering", "Electrical Engineering",
        "Civil Engineering", "Electronics and Communication", "Information Technology",
        "Chemical Engineering", "Biomedical Engineering"
    ]

    if request.method == 'POST':
        subjects = []
        marks = []
        
        for i in range(1, 6):
            subject = request.form.get(f'subject{i}')
            mark = request.form.get(f'marks{i}')
            subjects.append(subject)
            marks.append(mark)

        hackathons = request.form.get('hackathons')

        # Process the data (Store in DB or use for recommendation)
        print("Subjects:", subjects)
        print("Marks:", marks)
        print("Hackathons:", hackathons)

        flash("Data Submitted Successfully!", "success")
        return redirect(url_for('job_recommendation'))

    return render_template('job_recommendation.html', engineering_subjects=engineering_subjects)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/careers')
def careers():
    search_query = request.args.get('search', '')
    if search_query:
        careers = Career.query.filter(Career.title.ilike(f'%{search_query}%')).all()
    else:
        careers = Career.query.all()
    return render_template('careers.html', careers=careers)

@app.route('/assessment/<type>')
@login_required
def take_assessment(type):
    return render_template(f'assessments/{type}.html')

@app.route('/submit_assessment', methods=['POST'])
@login_required
def submit_assessment():
    assessment_type = request.form.get('type')
    score = float(request.form.get('score'))
    
    new_assessment = Assessment(
        user_id=current_user.id,
        assessment_type=assessment_type,
        score=score
    )
    
    db.session.add(new_assessment)
    db.session.commit()
    
    flash('Assessment submitted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)