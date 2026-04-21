from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import random
import os
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from forms import RegistrationForm, LoginForm, QuestForm, TrophyForm

# If the db gets deleted you will have to create a new one using the terminal:
# flask init-db to initialize a new one
# flask create-admin to create the admin

# Load variables from .env
load_dotenv()


# Initialize the Flask app
app = Flask(__name__, template_folder='template')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-key-for-dev-only')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///questlog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and LoginManager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore
csrf = CSRFProtect(app)

# Utility functions

def flash_redirect(message, category, route):
    flash(message, category)
    return redirect(url_for(route))

def calculate_level(xp):
    return int((xp / 100) ** 0.5) + 1

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return flash_redirect('You need admin privileges to access this page.', 'error', 'index')
        return f(*args, **kwargs)
    return decorated_function

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(10), default='user', nullable=False)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    user_quests = db.relationship('UserQuest', backref='user', lazy=True)
    user_trophies = db.relationship('UserTrophy', backref='user', lazy=True)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def __repr__(self):
        return f'<User {self.username}>'

class Quest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    xp_reward = db.Column(db.Integer, default=10)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    user_quests = db.relationship('UserQuest', backref='quest', lazy=True)

    def __init__(self, **kwargs):
        super(Quest, self).__init__(**kwargs)

    def __repr__(self):
        return f'<Quest {self.name}>'

class UserQuest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False)
    status = db.Column(db.String(20), default='active')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    xp_earned = db.Column(db.Integer, default=0)

    def __init__(self, **kwargs):
        super(UserQuest, self).__init__(**kwargs)

    def __repr__(self):
        return f'<UserQuest User:{self.user_id} Quest:{self.quest_id}>'

class Trophy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    icon = db.Column(db.String(100), default='🏆')
    requirement_type = db.Column(db.String(50), nullable=False)
    requirement_value = db.Column(db.Integer, nullable=False)
    xp_reward = db.Column(db.Integer, default=50)

    user_trophies = db.relationship('UserTrophy', backref='trophy', lazy=True)

    def __init__(self, **kwargs):
        super(Trophy, self).__init__(**kwargs)

    def __repr__(self):
        return f'<Trophy {self.name}>'

class UserTrophy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trophy_id = db.Column(db.Integer, db.ForeignKey('trophy.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(UserTrophy, self).__init__(**kwargs)

    def __repr__(self):
        return f'<UserTrophy User:{self.user_id} Trophy:{self.trophy_id}>'

# Trophies logic

def check_trophies(user):
    trophies = Trophy.query.all()
    user_trophy_ids = {ut.trophy_id for ut in UserTrophy.query.filter_by(user_id=user.id).all()}
    newly_earned = []

    for trophy in trophies:
        if trophy.id in user_trophy_ids:
            continue

        earned = False
        if trophy.requirement_type == 'quests_completed':
            earned = UserQuest.query.filter_by(user_id=user.id, status='completed').count() >= trophy.requirement_value
        elif trophy.requirement_type == 'level_reached':
            earned = user.level >= trophy.requirement_value
        elif trophy.requirement_type == 'xp_earned':
            earned = user.xp >= trophy.requirement_value

        if earned:
            # Add the new trophy relationship to the session, but don't commit yet.
            db.session.add(UserTrophy(user_id=user.id, trophy_id=trophy.id))
            user.xp += trophy.xp_reward
            newly_earned.append(trophy)
    
    # The commit will be handled by the calling function (e.g., complete_quest)
    # to ensure the entire operation is atomic.
    return newly_earned

# Routes

@app.route('/')
def home():
    return redirect(url_for('index') if current_user.is_authenticated else 'login')

@app.route('/index')
@login_required
def index():
    user_quests = UserQuest.query.filter_by(user_id=current_user.id, status='active').all()
    print(f"Found {len(user_quests)} user quests for user {current_user.id}")
    
    active_quests = []
    for uq in user_quests:
        if uq.quest and uq.quest.is_active:
            quest_data = {
                'id': uq.id,
                'quest_id': uq.quest.id,
                'name': uq.quest.name,
                'description': uq.quest.description,
                'category': uq.quest.category,
                'difficulty': uq.quest.difficulty,
                'xp_reward': uq.quest.xp_reward,
                'started_at': uq.started_at
            }
            active_quests.append(quest_data)
            print(f"Added quest: {uq.quest.name} (ID: {uq.id})")
        else:
            print(f"Skipped quest: quest is None or inactive")
    
    print(f"Total active quests: {len(active_quests)}")
    return render_template('index.html', active_quests=active_quests, user_xp=current_user.xp, user_level=current_user.level)

@app.route('/add_quest', methods=['GET','POST'])
@login_required
@admin_required
def add_quest():
    form = QuestForm()
    if form.validate_on_submit():
        new_quest = Quest(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
            difficulty=form.difficulty.data,
            xp_reward=form.xp_reward.data,
            created_by=current_user.id
        )
        db.session.add(new_quest)
        db.session.commit()
        return flash_redirect('Quest added successfully!', 'success', 'admin_dashboard')

    return render_template('quest_form.html', form=form, action='Add')

@app.route('/edit_quest/<int:quest_id>', methods=['GET','POST'])
@login_required
@admin_required
def edit_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    form = QuestForm(obj=quest)
    if form.validate_on_submit():
        quest.name = form.name.data
        quest.description = form.description.data
        quest.category = form.category.data
        quest.difficulty = form.difficulty.data
        quest.xp_reward = form.xp_reward.data
        db.session.commit()
        return flash_redirect('Quest updated successfully!', 'success', 'admin_dashboard')

    return render_template('quest_form.html', form=form, action='Edit', quest=quest)

@app.route('/delete_quest/<int:quest_id>', methods=['POST'])
@login_required
@admin_required
def delete_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    quest.is_active = False
    db.session.commit()
    return flash_redirect('Quest deactivated successfully!', 'success', 'admin_dashboard')

@app.route('/complete_quest/<int:user_quest_id>', methods=['POST'])
@login_required
def complete_quest(user_quest_id):
    uq = UserQuest.query.get_or_404(user_quest_id)
    if uq.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not authorized'}), 403
    if uq.status == 'completed':
        return jsonify({'success': False, 'error': 'Quest already completed'}), 400

    current_user.xp += uq.quest.xp_reward
    uq.status = 'completed'
    uq.completed_at = datetime.utcnow()
    uq.xp_earned = uq.quest.xp_reward
    
    # Check for trophies before level calculation
    newly_earned_trophies = check_trophies(current_user)
    
    # Recalculate level after potential XP gain from trophies
    current_user.level = calculate_level(current_user.xp)
    db.session.commit()
    
    trophy_data = [{
        'name': t.name, 
        'description': t.description, 
        'icon': t.icon,
        'xp_reward': t.xp_reward
    } for t in newly_earned_trophies]

    return jsonify({
        'success': True, 
        'message': f'Quest completed! You earned {uq.quest.xp_reward} XP!',
        'new_xp': current_user.xp,
        'new_level': current_user.level,
        'earned_trophies': trophy_data
    })

@app.route('/generate_random_quest', methods=['POST'])
@login_required
def generate_random_quest():
    category = request.form.get('category', 'drawing')
    difficulty = request.form.get('difficulty', 'easy')
    available = Quest.query.filter_by(category=category, difficulty=difficulty, is_active=True).all()
    if not available:
        return jsonify({'success': False, 'error': 'No quests available for this category and difficulty.'})
    quest = random.choice(available)
    return jsonify({
        'success': True,
        'quest': {
            'name': quest.name,
            'description': quest.description,
            'category': quest.category,
            'difficulty': quest.difficulty,
            'xp_reward': quest.xp_reward
        }
    })

@app.route('/add_random_quest', methods=['POST'])
@login_required
def add_random_quest():
    name = request.form.get('name')
    description = request.form.get('description', f"Custom quest: {name}")
    category = request.form.get('category', 'drawing')
    difficulty = request.form.get('difficulty', 'easy')
    
    if not name:
        return jsonify({'success': False, 'error': 'Quest name is required.'})
    
    # Calculate XP reward based on difficulty
    xp_reward = {'easy': 10, 'medium': 20, 'hard': 30}.get(difficulty, 10)
    
    # Check if this exact quest already exists
    existing_quest = Quest.query.filter_by(
        name=name, 
        category=category, 
        difficulty=difficulty,
        is_active=True
    ).first()
    
    if existing_quest:
        quest = existing_quest
    else:
        # Create a new quest
        quest = Quest(
            name=name,
            description=description,
            category=category,
            difficulty=difficulty,
            xp_reward=xp_reward,
            created_by=current_user.id,
            is_active=True
        )
        db.session.add(quest)
        db.session.flush()  # Get the ID
    
    # Check if user already has this quest active
    existing_user_quest = UserQuest.query.filter_by(
        user_id=current_user.id,
        quest_id=quest.id,
        status='active'
    ).first()
    
    if existing_user_quest:
        return jsonify({'success': False, 'error': 'You already have this quest active.'})
    
    # Add quest to user's active quests
    user_quest = UserQuest(
        user_id=current_user.id,
        quest_id=quest.id,
        status='active'
    )
    db.session.add(user_quest)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Quest added successfully!',
        'quest_id': user_quest.id
    })

@app.route('/trophies')
@login_required
def trophies():
    user_trophies = UserTrophy.query.filter_by(user_id=current_user.id).all()
    earned_trophies = []
    for ut in user_trophies:
        trophy = Trophy.query.get(ut.trophy_id)
        if trophy:
            earned_trophies.append({
                'name': trophy.name,
                'description': trophy.description,
                'icon': trophy.icon,
                'earned_at': ut.earned_at
            })
    
    # Get all trophies to show which ones are locked
    all_trophies = Trophy.query.all()
    all_trophy_data = []
    for trophy in all_trophies:
        earned = any(ut.trophy_id == trophy.id for ut in user_trophies)
        all_trophy_data.append({
            'name': trophy.name,
            'description': trophy.description,
            'icon': trophy.icon,
            'earned': earned,
            'requirement_type': trophy.requirement_type,
            'requirement_value': trophy.requirement_value
        })
    
    return render_template('trophies.html', trophies=all_trophy_data)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Get statistics
    total_users = User.query.filter_by(is_active=True).count()
    total_quests = Quest.query.filter_by(is_active=True).count()
    total_completed_quests = UserQuest.query.filter_by(status='completed').count()
    admin_users = User.query.filter_by(role='admin').count()
    
    stats = {
        'total_users': total_users,
        'total_quests': total_quests,
        'total_completed_quests': total_completed_quests,
        'admin_users': admin_users
    }
    
    # Get all items for management
    users = User.query.filter_by(is_active=True).all()
    quests = Quest.query.filter_by(is_active=True).all()
    trophies = Trophy.query.all()
    
    return render_template('admin_dashboard.html', stats=stats, users=users, quests=quests, trophies=trophies)

@app.route('/toggle_user_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    
    role_text = 'admin' if user.role == 'admin' else 'user'
    flash(f'User {user.username} role changed to {role_text}.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    username = user.username
    user.is_active = False
    db.session.commit()
    
    flash(f'User {username} deactivated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.is_active and form.password.data and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Incorrect username or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
        elif form.password.data:
            new_user = User(username=form.username.data, password=generate_password_hash(form.password.data))
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables and initializes trophies."""
    db.create_all()
    
    trophies_data = [
        {'name': 'First Steps', 'description': 'Complete your first quest', 'requirement_type': 'quests_completed', 'requirement_value': 1, 'icon': '🥇'},
        {'name': 'Quest Master', 'description': 'Complete 10 quests', 'requirement_type': 'quests_completed', 'requirement_value': 10, 'icon': '🏆'},
        {'name': 'Level 5', 'description': 'Reach level 5', 'requirement_type': 'level_reached', 'requirement_value': 5, 'icon': '⭐'},
        {'name': 'XP Collector', 'description': 'Earn 1000 XP', 'requirement_type': 'xp_earned', 'requirement_value': 1000, 'icon': '💎'},
        {'name': 'Legendary', 'description': 'Reach level 10', 'requirement_type': 'level_reached', 'requirement_value': 10, 'icon': '👑'},
    ]
    
    for trophy_data in trophies_data:
        existing = Trophy.query.filter_by(name=trophy_data['name']).first()
        if not existing:
            trophy = Trophy(**trophy_data)
            db.session.add(trophy)
    
    db.session.commit()
    print('Database and trophies initialized.')

@app.cli.command('create-admin')
def create_admin_command():
    """Creates the admin user."""
    admin_username = 'admin'
    if User.query.filter_by(username=admin_username).first():
        print(f'User {admin_username} already exists.')
        return
    
    password = 'changethis' # In a real app, prompt for this
    admin = User(username=admin_username, password=generate_password_hash(password), role="admin")
    db.session.add(admin)
    db.session.commit()
    print(f'Admin user {admin_username} created. PLEASE CHANGE THE DEFAULT PASSWORD.')

# Trophy Management Routes
@app.route('/add_trophy', methods=['GET', 'POST'])
@login_required
@admin_required
def add_trophy():
    form = TrophyForm()
    if form.validate_on_submit():
        new_trophy = Trophy(
            name=form.name.data,
            description=form.description.data,
            icon=form.icon.data,
            requirement_type=form.requirement_type.data,
            requirement_value=form.requirement_value.data,
            xp_reward=form.xp_reward.data
        )
        db.session.add(new_trophy)
        db.session.commit()
        flash('Trophy added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('trophy_form.html', form=form, action='Add')

@app.route('/edit_trophy/<int:trophy_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_trophy(trophy_id):
    trophy = Trophy.query.get_or_404(trophy_id)
    form = TrophyForm(obj=trophy)
    if form.validate_on_submit():
        trophy.name = form.name.data
        trophy.description = form.description.data
        trophy.icon = form.icon.data
        trophy.requirement_type = form.requirement_type.data
        trophy.requirement_value = form.requirement_value.data
        trophy.xp_reward = form.xp_reward.data
        db.session.commit()
        flash('Trophy updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('trophy_form.html', form=form, action='Edit')

@app.route('/delete_trophy/<int:trophy_id>', methods=['POST'])
@login_required
@admin_required
def delete_trophy(trophy_id):
    trophy = Trophy.query.get_or_404(trophy_id)
    # Also delete associated UserTrophy records
    UserTrophy.query.filter_by(trophy_id=trophy.id).delete()
    db.session.delete(trophy)
    db.session.commit()
    flash('Trophy deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)