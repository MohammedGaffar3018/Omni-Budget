from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os

from database import get_db, close_db, init_db

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Define profile configurations
PROFILES = {
    'explorer': {
        'name': 'Explorer',
        'age_range': '6-12',
        'theme': 'explorer',
        'income_categories': ['Pocket Money', 'Gifts', 'Chores'],
        'expense_categories': ['Toys', 'Snacks', 'Games', 'Books'],
        'budget_type': 'Piggy Bank'
    },
    'pacer': {
        'name': 'Pacer',
        'age_range': '13-22',
        'theme': 'pacer',
        'income_categories': ['Freelance', 'Internship', 'Part-time Job', 'Allowance'],
        'expense_categories': ['Food', 'Recharge', 'Entertainment', 'Transport', 'Shopping'],
        'budget_type': 'Buckets'
    },
    'builder': {
        'name': 'Builder',
        'age_range': '23-60',
        'theme': 'builder',
        'income_categories': ['Salary', 'Business', 'Investments', 'Rental Income'],
        'expense_categories': ['EMI', 'Rent', 'Groceries', 'Utilities', 'Insurance', 'Education'],
        'budget_type': 'Zero-Based Budgeting'
    },
    'guardian': {
        'name': 'Guardian',
        'age_range': '60+',
        'theme': 'guardian',
        'income_categories': ['Pension', 'Interest', 'Dividends', 'Rental Income'],
        'expense_categories': ['Medicine', 'Healthcare', 'Gifts', 'Utilities', 'Groceries'],
        'budget_type': 'Monthly Cash Flow'
    }
}

# Initialize database
with app.app_context():
    init_db()

# Teardown database connection
app.teardown_appcontext(close_db)

# Helper function to get current user
def get_current_user():
    if 'user_id' in session:
        db = get_db()
        return db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return None

# Helper function to format currency
def format_currency(amount):
    return f"₹{amount:,.2f}"

# Add custom filters to Jinja2
@app.context_processor
def inject_custom_filters():
    return dict(format_currency=format_currency, profiles=PROFILES)

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password'
    
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        profile = request.form.get('profile', 'explorer')
        
        db = get_db()
        
        # Check if username already exists
        if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
            error = 'Username already exists'
        elif db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            error = 'Email already registered'
        else:
            # Create new user
            db.execute(
                'INSERT INTO users (username, email, password, current_profile) VALUES (?, ?, ?, ?)',
                (username, email, generate_password_hash(password), profile)
            )
            db.commit()
            
            # Log in the new user
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            session['user_id'] = user['id']
            
            return redirect(url_for('dashboard'))
    
    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    profile = user['current_profile']
    profile_config = PROFILES[profile]
    
    db = get_db()
    
    # Get recent transactions
    transactions = db.execute(
        'SELECT * FROM transactions WHERE user_id = ? AND profile = ? ORDER BY date DESC LIMIT 10',
        (user['id'], profile)
    ).fetchall()
    
    # Get budgets
    current_month = datetime.now().month
    current_year = datetime.now().year
    budgets = db.execute(
        'SELECT * FROM budgets WHERE user_id = ? AND profile = ? AND month = ? AND year = ?',
        (user['id'], profile, current_month, current_year)
    ).fetchall()
    
    # Get savings goals
    savings_goals = db.execute(
        'SELECT * FROM savings_goals WHERE user_id = ? AND profile = ?',
        (user['id'], profile)
    ).fetchall()
    
    # Get badges for gamification
    badges = db.execute(
        'SELECT * FROM gamification WHERE user_id = ? AND profile = ?',
        (user['id'], profile)
    ).fetchall()
    
    # Calculate totals
    total_income = db.execute(
        'SELECT SUM(amount) as total FROM transactions WHERE user_id = ? AND profile = ? AND type = ? AND month = ? AND year = ?',
        (user['id'], profile, 'income', current_month, current_year)
    ).fetchone()['total'] or 0
    
    total_expense = db.execute(
        'SELECT SUM(amount) as total FROM transactions WHERE user_id = ? AND profile = ? AND type = ? AND month = ? AND year = ?',
        (user['id'], profile, 'expense', current_month, current_year)
    ).fetchone()['total'] or 0
    
    return render_template(
        'dashboard.html',
        user=user,
        profile=profile,
        profile_config=profile_config,
        transactions=transactions,
        budgets=budgets,
        savings_goals=savings_goals,
        badges=badges,
        total_income=total_income,
        total_expense=total_expense
    )

@app.route('/switch_profile/<profile>')
def switch_profile(profile):
    if profile not in PROFILES:
        return redirect(url_for('dashboard'))
    
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute('UPDATE users SET current_profile = ? WHERE id = ?', (profile, user['id']))
    db.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    profile = user['current_profile']
    trans_type = request.form.get('type')
    category = request.form.get('category')
    amount = float(request.form.get('amount'))
    description = request.form.get('description', '')
    
    db = get_db()
    db.execute(
        'INSERT INTO transactions (user_id, profile, type, category, amount, description) VALUES (?, ?, ?, ?, ?, ?)',
        (user['id'], profile, trans_type, category, amount, description)
    )
    db.commit()
    
    # Update budget if applicable
    if trans_type == 'expense':
        current_month = datetime.now().month
        current_year = datetime.now().year
        budget = db.execute(
            'SELECT * FROM budgets WHERE user_id = ? AND profile = ? AND category = ? AND month = ? AND year = ?',
            (user['id'], profile, category, current_month, current_year)
        ).fetchone()
        
        if budget:
            db.execute(
                'UPDATE budgets SET spent = spent + ? WHERE id = ?',
                (amount, budget['id'])
            )
            db.commit()
    
    # Award badges for gamification
    if profile == 'explorer':
        # Check for first transaction badge
        trans_count = db.execute(
            'SELECT COUNT(*) as count FROM transactions WHERE user_id = ? AND profile = ?',
            (user['id'], profile)
        ).fetchone()['count']
        
        if trans_count == 1:
            db.execute(
                'INSERT INTO gamification (user_id, profile, badge_name, badge_icon) VALUES (?, ?, ?, ?)',
                (user['id'], profile, 'First Transaction', '🎉')
            )
            db.commit()
    
    return jsonify({'success': True})

@app.route('/add_budget', methods=['POST'])
def add_budget():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    profile = user['current_profile']
    category = request.form.get('category')
    amount = float(request.form.get('amount'))
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    db = get_db()
    
    # Check if budget already exists for this category and month
    existing_budget = db.execute(
        'SELECT * FROM budgets WHERE user_id = ? AND profile = ? AND category = ? AND month = ? AND year = ?',
        (user['id'], profile, category, current_month, current_year)
    ).fetchone()
    
    if existing_budget:
        db.execute(
            'UPDATE budgets SET amount = ? WHERE id = ?',
            (amount, existing_budget['id'])
        )
    else:
        db.execute(
            'INSERT INTO budgets (user_id, profile, category, amount, spent, month, year) VALUES (?, ?, ?, ?, 0, ?, ?)',
            (user['id'], profile, category, amount, current_month, current_year)
        )
    
    db.commit()
    
    return jsonify({'success': True})

@app.route('/add_savings_goal', methods=['POST'])
def add_savings_goal():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    profile = user['current_profile']
    name = request.form.get('name')
    target_amount = float(request.form.get('target_amount'))
    
    db = get_db()
    db.execute(
        'INSERT INTO savings_goals (user_id, profile, name, target_amount) VALUES (?, ?, ?, ?)',
        (user['id'], profile, name, target_amount)
    )
    db.commit()
    
    return jsonify({'success': True})

@app.route('/update_savings_goal', methods=['POST'])
def update_savings_goal():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    goal_id = request.form.get('goal_id')
    amount = float(request.form.get('amount'))
    
    db = get_db()
    db.execute(
        'UPDATE savings_goals SET current_amount = current_amount + ? WHERE id = ? AND user_id = ?',
        (amount, goal_id, user['id'])
    )
    db.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)