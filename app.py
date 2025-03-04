from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pickle
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import random
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user

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

import random
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user

# Sample set of 100 questions (Store this in a JSON file for better management)
QUESTIONS_FILE = "aptitude_questions.json"

# Load all questions from JSON file
def load_questions():
    with open(QUESTIONS_FILE, "r") as f:
        return json.load(f)

@app.route('/aptitude_test', methods=['GET', 'POST'])
@login_required
def aptitude_test():
    questions = load_questions()
    
    # Select 10 random questions each time
    selected_questions = random.sample(questions, 10)

    if request.method == 'POST':
        # Get user answers from form
        user_answers = request.form
        correct_answers = {q["id"]: q["answer"] for q in selected_questions}
        
        score = sum(10 for q_id in correct_answers if user_answers.get(q_id) == correct_answers[q_id])

        flash(f"You scored {score} out of 100!", "success")
        return redirect(url_for('dashboard'))
    
    return render_template('aptitude_test.html', questions=selected_questions)



# Load and Train ML Model (only once)
def train_model():
    df = pd.read_csv("Student Placement.csv")  # Ensure this file is uploaded
    label_encoder = LabelEncoder()
    df['Profile'] = label_encoder.fit_transform(df['Profile'])

    X = df[['DSA', 'DBMS', 'OS', 'CN', 'Mathmetics', 'Aptitute', 'Comm', 'Problem Solving', 'Creative', 'Hackathons']]
    y = df['Profile']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Save Model & Encoder
    with open('job_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('label_encoder.pkl', 'wb') as f:
        pickle.dump(label_encoder, f)

# Train Model
train_model()

@app.route('/job_recommendation', methods=['GET', 'POST'])
@login_required
def job_recommendation():
    if request.method == 'POST':
        # Get user inputs
        user_data = [
            int(request.form.get('DSA')),
            int(request.form.get('DBMS')),
            int(request.form.get('OS')),
            int(request.form.get('CN')),
            int(request.form.get('Mathmetics')),
            int(request.form.get('Aptitute')),
            int(request.form.get('Comm')),
            int(request.form.get('Problem_Solving')),
            int(request.form.get('Creative')),
            int(request.form.get('Hackathons'))
        ]

        # Load model and encoder
        with open('job_model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('label_encoder.pkl', 'rb') as f:
            label_encoder = pickle.load(f)

        # Predict job profile
        predicted_profile = model.predict([user_data])
        job_role = label_encoder.inverse_transform(predicted_profile)[0]

        flash(f"Recommended Job Role: {job_role}", "success")
        return redirect(url_for('job_recommendation'))

    return render_template('job_recommendation.html')


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