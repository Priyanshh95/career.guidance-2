from flask import Flask, render_template, request, jsonify,redirect, url_for, flash, session
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
from scrape_careers import scrape_career_details
import re
import subprocess
import random
import openai
from dotenv import load_dotenv
import os

from flask_login import login_required, current_user

load_dotenv()  # Load env vars

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = 'your_secret_key'

questions = [
    "Reverse a string.",
    "Check if a number is a prime number.",
    "Print the first n terms of the Fibonacci series.",
    "Find the factorial of a number.",
    "Check if a number is a palindrome.",
    "Find the largest element in an array.",
    "Calculate the sum of digits of a number.",
    "Count the number of vowels in a string.",
    "Check if a number is an Armstrong number.",
    "Sort an array using Bubble Sort."
]

# Expected outputs for some questions (you can expand this based on your requirements)
expected_outputs = {
    "Reverse a string.": "gnirts",
    "Check if a number is a prime number.": "Prime",  # For example: if input is 7, output would be 'Prime'
    "Find the factorial of a number.": "120",  # For input 5
    "Check if a number is a palindrome.": "Palindrome",  # For example: input 121
    "Find the largest element in an array.": "9",  # For array [1, 9, 3]
    "Calculate the sum of digits of a number.": "15",  # For input 567
    "Count the number of vowels in a string.": "3",  # For input "hello"
    "Check if a number is an Armstrong number.": "Armstrong",  # For input 153
    "Sort an array using Bubble Sort.": "1 2 3 4 5"  # For input array [5, 4, 3, 2, 1]
}

@app.route('/coding_test', methods=['GET', 'POST'])
def coding_test():
    output = None
    code = ""
    custom_input = ""
    marks = 0
    
    # Set the question only if it's not already in the session
    if 'question' not in session:
        session['question'] = random.choice(questions)
    
    question = session['question']

    if request.method == 'POST':
        code = request.form['code']
        custom_input = request.form.get('custom_input', '')
        try:
            with open("user_code.cpp", "w") as f:
                f.write(code)

            compile_result = subprocess.run(["g++", "user_code.cpp", "-o", "user_code.out"], capture_output=True, text=True)

            if compile_result.returncode != 0:
                output = compile_result.stderr
            else:
                run_result = subprocess.run(
                    ["./user_code.out"],
                    input=custom_input.strip(),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = run_result.stdout

                # Evaluate the output and assign marks based on correctness
                if output.strip() == expected_outputs.get(question, "").strip():
                    marks = 100
                else:
                    marks = 50  # For incorrect answers, you can assign partial marks

        except subprocess.TimeoutExpired:
            output = "⏱️ Time Limit Exceeded"
        except Exception as e:
            output = str(e)

    return render_template("coding_test.html", output=output, code=code, custom_input=custom_input, question=question, marks=marks)


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
    year = datetime.now().year
    return render_template('index.html', year=year)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

# Password strength checker function
def is_strong_password(password):
    # Minimum 8 characters, at least one uppercase, one lowercase, one digit, one special character
    pattern = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    )
    return pattern.match(password) is not None

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check password match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('signup'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('signup'))

        # Server-side password strength validation
        strong_password = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
        if not strong_password.match(password):
            flash('Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character.', 'danger')
            return redirect(url_for('signup'))

        # Create user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Sample set of 100 questions (Store this in a JSON file for better management)
QUESTIONS_FILE = "aptitude_questions.json"

# Load all questions from JSON file
def load_questions():
    with open(QUESTIONS_FILE, "r") as f:
        return json.load(f)

@app.route('/aptitude_test', methods=['GET', 'POST'])
@login_required
def aptitude_test():
    if request.method == 'POST':
        # Retrieve stored questions from session
        selected_questions = session.get('selected_questions', [])
        if not selected_questions:
            flash("Session expired! Please retake the test.", "error")
            return redirect(url_for('aptitude_test'))

        # Extract user answers from form submission
        user_answers = request.form

        # Extract correct answers from stored questions
        correct_answers = {q["id"]: q["answer"] for q in selected_questions}

        # Compute score
        score = sum(
            10 for q_id, correct_ans in correct_answers.items()
            if user_answers.get(q_id, "").strip() == correct_ans.strip()
        )

        # Save the score in database
        new_assessment = Assessment(user_id=current_user.id, assessment_type='Aptitude Test', score=score)
        db.session.add(new_assessment)
        db.session.commit()

        flash(f"You scored {score // 10} out of 10!", "success")
        return redirect(url_for('index'))

    # GET request: Select 10 random questions and store in session
    questions = load_questions()
    selected_questions = random.sample(questions, 10)
    session['selected_questions'] = selected_questions  # Store in session for later grading

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
@app.route('/job/<job_name>')
def job_detail(job_name):
    job_info = get_job_info_llm(job_name)
    roadmap = get_roadmap_llm(job_name)  # << USE get_roadmap_llm here, not show_roadmap
    return render_template("job_detail.html", job_name=job_name, job_info=job_info, roadmap=roadmap)


def get_job_info_llm(job_name):
    prompt = f"""
    Give detailed information about the job role '{job_name}' in the following JSON format:
    {{
        "title": "",
        "description": "",
        "skills": [],
        "responsibilities": [],
        "education": "",
        "salary": "",
        "outlook": ""
    }}
    Make it detailed and professional.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",   # or "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are a career guidance expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # lower means more accurate and consistent
            max_tokens=1000
        )
        content = response['choices'][0]['message']['content']
        # Since content will be a string (looking like JSON), safely evaluate it:
        import json
        job_info = json.loads(content)
        return job_info
    except Exception as e:
        print(e)
        return {
            "title": job_name,
            "description": "No detailed information could be retrieved at the moment.",
            "skills": [],
            "responsibilities": [],
            "education": "N/A",
            "salary": "N/A",
            "outlook": "N/A"
        }


@app.route('/roadmap/<job_role>', methods=['GET'])
def show_roadmap(job_role):
    roadmap = get_roadmap_llm(job_role)
    return render_template("roadmap.html", job_role=job_role, roadmap=roadmap)

# Pure function that returns dict
def get_roadmap_llm(job_role):
    prompt = f"""
    You are an expert career counselor.

    Generate a detailed 5-step learning roadmap for becoming a successful '{job_role}'.

    Each step should include:
    - Task (what to do)
    - Weeks (how many weeks needed)
    - 3 Recommended Resources (courses, books, tools, or websites)

    Format your response strictly in JSON as follows:
    {{
        "step_1": {{"task": "", "weeks": , "resources": ["", "", ""]}},
        "step_2": {{"task": "", "weeks": , "resources": ["", "", ""]}},
        "step_3": {{"task": "", "weeks": , "resources": ["", "", ""]}},
        "step_4": {{"task": "", "weeks": , "resources": ["", "", ""]}},
        "step_5": {{"task": "", "weeks": , "resources": ["", "", ""]}}
    }}

    Only output the JSON. No extra explanations.
    """
    response = call_llm(prompt)
    import json
    roadmap = json.loads(response)
    return roadmap


openai.api_key = os.getenv("OPENAI_API_KEY") 
def call_llm(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",  # or "gpt-3.5-turbo" if you want cheaper and faster
        messages=[
            {"role": "system", "content": "You are a helpful assistant that returns only JSON formatted learning roadmaps."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,  # low randomness for predictable output
        max_tokens=1000   # enough space for detailed steps
    )
    return response['choices'][0]['message']['content']

@app.route('/job_recommendation', methods=['GET', 'POST'])
@login_required
def job_recommendation():
    test_scores = {}  # Default empty dictionary for test_scores

    if request.method == 'POST':
        # Get user inputs and convert to float first, then to int
        user_data = [
            int(float(request.form.get('DSA', 0))),
            int(float(request.form.get('DBMS', 0))),
            int(float(request.form.get('OS', 0))),
            int(float(request.form.get('CN', 0))),
            int(float(request.form.get('Mathmetics', 0))),
            int(float(request.form.get('Aptitute', 0))),
            int(float(request.form.get('Comm', 0))),
            int(float(request.form.get('Problem_Solving', 0))),
            int(float(request.form.get('Creative', 0))),
            int(float(request.form.get('Hackathons', 0)))
        ]

        # Load model and encoder
        with open('job_model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('label_encoder.pkl', 'rb') as f:
            label_encoder = pickle.load(f)

        # Predict job profile
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba([user_data])[0]
            top_3_indices = probabilities.argsort()[-3:][::-1]
            top_3_jobs = label_encoder.inverse_transform(top_3_indices).tolist()
        else:
            predicted_profile = model.predict([user_data])
            top_3_jobs = label_encoder.inverse_transform(predicted_profile).tolist()

        return render_template('job_recommendation.html', job_predictions=top_3_jobs, test_scores=test_scores)

    # ✅ Correct indentation here (GET method)
    aptitude = Assessment.query.filter_by(user_id=current_user.id, assessment_type='Aptitude Test').order_by(Assessment.date_taken.desc()).first()
    communication = Assessment.query.filter_by(user_id=current_user.id, assessment_type='Communication Test').order_by(Assessment.date_taken.desc()).first()
    problem_solving = Assessment.query.filter_by(user_id=current_user.id, assessment_type='Coding Test').order_by(Assessment.date_taken.desc()).first()
    creative = Assessment.query.filter_by(user_id=current_user.id, assessment_type='Creativity Test').order_by(Assessment.date_taken.desc()).first()

    test_scores = {
        "Aptitute": aptitude.score if aptitude else 0,
        "Comm": communication.score if communication else 0,
        "Problem_Solving": problem_solving.score if problem_solving else 0,
        "Creative": creative.score if creative else 0
    }

    return render_template('job_recommendation.html', test_scores=test_scores)


# Load job data at startup
with open('static/data/2024.json') as f:
    data_2024 = json.load(f)

with open('static/data/2025.json') as f:
    data_2025 = json.load(f)

@app.route('/job-profile')
def job_profile():
    return render_template('job_profile.html')

@app.route('/get-jobs/<year>')
def get_jobs(year):
    if year == '2024':
        return jsonify(data_2024)
    elif year == '2025':
        return jsonify(data_2025)
    else:
        return jsonify({"error": "Invalid year"}), 404

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

PROMPTS = [
    "Write a story about a world where dreams come true.",
    "Describe a day in the life of a time traveler.",
    "A mysterious door appears in your house. What happens next?",
    "You wake up with a superpower. What is it and how do you use it?"
]

def get_prompt():
    return random.choice(PROMPTS)

def check_grammar(story):
    issues = len(re.findall(r'\b(is|are|was|were)\s+a\b', story, re.IGNORECASE))
    return issues

def assess_creativity(story):
    unique_words = set(story.split())
    return min(10, len(unique_words) // 10)

def assess_coherence(story):
    sentences = re.split(r'[.!?]', story)
    return min(10, len(set(sentences)) // 5)

def assess_engagement(story):
    length = len(story.split())
    sentences = re.split(r'[.!?]', story)
    return min(10, (length + len(set(sentences))) // 20)

def get_feedback(story):
    score = (assess_creativity(story) + assess_coherence(story) + (10 - check_grammar(story)) + assess_engagement(story)) / 4
    return f"Overall Score: {score:.2f}/10", score

@app.route('/creativity_test', methods=['GET', 'POST'])
@login_required
def creativity_test():
    if request.method == 'POST':
        data = request.get_json()
        story = data.get("story", "")
        feedback, score = get_feedback(story)
        
        new_assessment = Assessment(user_id=current_user.id, assessment_type='Creativity Test', score=score)
        db.session.add(new_assessment)
        db.session.commit()
        
        return jsonify({"feedback": feedback, "score": score})
    
    return render_template('creativity_test.html', prompt=get_prompt())

@app.route('/communication_test', methods=['GET', 'POST'])
@login_required
def communication_test():
    if request.method == 'POST':
        data = request.get_json()
        response = data.get("text", "")
        feedback, score = get_feedback(response)
        
        new_assessment = Assessment(user_id=current_user.id, assessment_type='Communication Test', score=score)
        db.session.add(new_assessment)
        db.session.commit()
        
        return jsonify({"feedback": feedback, "score": score})
    
    return render_template('communication_test.html')


@app.route('/careers', methods=['GET', 'POST'])
def careers():
    career_info = None  # Default to None

    if request.method == "POST":
        career_name = request.form.get("career_name")  # Get input safely
        if career_name:
            career_info = scrape_career_details(career_name)  # Fetch details

    return render_template("careers.html", career_info=career_info)

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

@app.route('/industry_trends', methods=['GET', 'POST'])
def industry_trends():
    job_info = None
    if request.method == 'POST':
        job_role = request.form.get('job_role')
        trend_data = get_industry_trends_llm(job_role)
        job_info = {
            'role': job_role,
            'description': trend_data.get("description", "No description available."),
            'trend_score': trend_data.get("trend_score", "N/A"),
            'companies': trend_data.get("companies", []),
            'salary': trend_data.get("salary", "Not available")
        }
    return render_template('industry_trends.html', job_info=job_info)

def get_industry_trends_llm(job_role):
    prompt = f"""
    You are an expert career analyst.

    Provide the latest industry trends for the job role '{job_role}' in the following JSON format:

    {{
        "description": "A detailed description about current trends and demands in this role.",
        "trend_score": "A score from 1 to 10 indicating how trending this role is currently.",
        "companies": ["Company1", "Company2", "Company3"],  // Top companies hiring for this role
        "salary": "Average salary range globally or country-wise."
    }}

    Be realistic and professional. 
    ONLY output the JSON without any extra explanation.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you want more accurate
            messages=[
                {"role": "system", "content": "You are a career trends and industry analysis expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        content = response['choices'][0]['message']['content']
        import json
        trend_data = json.loads(content)
        return trend_data
    except Exception as e:
        print(e)
        return {
            "description": "Could not fetch industry trends at the moment.",
            "trend_score": "N/A",
            "companies": [],
            "salary": "N/A"
        }

@app.route('/self_assessment')
def self_assessment():
    return render_template('self_assessment.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)