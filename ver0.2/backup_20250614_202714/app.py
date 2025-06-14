from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gtr.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lap_times = db.relationship('LapTime', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class GameTitle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lap_times = db.relationship('LapTime', backref='game_title', lazy=True)

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    game_title_id = db.Column(db.Integer, db.ForeignKey('game_title.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lap_times = db.relationship('LapTime', backref='car', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    game_title_id = db.Column(db.Integer, db.ForeignKey('game_title.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lap_times = db.relationship('LapTime', backref='course', lazy=True)

class LapTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_title_id = db.Column(db.Integer, db.ForeignKey('game_title.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    memo = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/lap-history')
@login_required
def lap_history():
    return render_template('lap_history.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')

    if not all([email, password, username]):
        return jsonify({'error': 'すべての項目を入力してください'}), 400

    # メールアドレスの形式チェック
    if not re.match(r'^kmc\d{4}@kamiyama\.ac\.jp$', email):
        return jsonify({'error': '無効なメールアドレス形式です'}), 400

    # パスワードの形式チェック
    if not re.match(r'^\d{4}$', password):
        return jsonify({'error': 'パスワードは4桁の数字で入力してください'}), 400

    # 既存ユーザーのチェック
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'このメールアドレスは既に登録されています'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'このユーザー名は既に使用されています'}), 400

    user = User(
        username=username,
        email=email
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': '登録が完了しました'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'error': 'メールアドレスとパスワードを入力してください'}), 400

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({'message': 'ログインに成功しました'}), 200

    return jsonify({'error': 'メールアドレスまたはパスワードが正しくありません'}), 401

@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/user')
@login_required
def get_user():
    return jsonify({
        'username': current_user.username,
        'created_at': current_user.created_at.isoformat()
    })

@app.route('/api/lap-times', methods=['GET'])
@login_required
def get_lap_times():
    lap_times = LapTime.query.filter_by(user_id=current_user.id).order_by(LapTime.created_at.desc()).all()
    return jsonify([{
        'id': lt.id,
        'game_title': lt.game_title.name,
        'car': lt.car.name,
        'course': lt.course.name,
        'time': lt.time,
        'memo': lt.memo,
        'created_at': lt.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for lt in lap_times])

@app.route('/api/lap-times', methods=['POST'])
@login_required
def add_lap_time():
    data = request.get_json()
    game_title_id = data.get('game_title_id')
    car_id = data.get('car_id')
    course_id = data.get('course_id')
    time = data.get('time')
    memo = data.get('memo', '')

    if not all([game_title_id, car_id, course_id, time]):
        return jsonify({'error': 'すべての項目を入力してください'}), 400

    lap_time = LapTime(
        user_id=current_user.id,
        game_title_id=game_title_id,
        car_id=car_id,
        course_id=course_id,
        time=time,
        memo=memo
    )
    db.session.add(lap_time)
    db.session.commit()

    return jsonify({
        'id': lap_time.id,
        'game_title': lap_time.game_title.name,
        'car': lap_time.car.name,
        'course': lap_time.course.name,
        'time': lap_time.time,
        'memo': lap_time.memo,
        'created_at': lap_time.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }), 201

@app.route('/api/lap-times/<int:lap_time_id>', methods=['DELETE'])
@login_required
def delete_lap_time(lap_time_id):
    lap_time = LapTime.query.get_or_404(lap_time_id)
    if lap_time.user_id != current_user.id:
        return jsonify({'error': 'このラップタイムを削除する権限がありません'}), 403

    db.session.delete(lap_time)
    db.session.commit()
    return jsonify({'message': 'ラップタイムを削除しました'}), 200

@app.route('/api/game-titles', methods=['GET'])
@login_required
def get_game_titles():
    game_titles = GameTitle.query.all()
    return jsonify([{'id': gt.id, 'name': gt.name} for gt in game_titles])

@app.route('/api/game-titles', methods=['POST'])
@login_required
def add_game_title():
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'ゲームタイトル名が必要です'}), 400
    
    if GameTitle.query.filter_by(name=name).first():
        return jsonify({'error': 'このゲームタイトルは既に存在します'}), 400
    
    game_title = GameTitle(name=name)
    db.session.add(game_title)
    db.session.commit()
    
    return jsonify({'id': game_title.id, 'name': game_title.name}), 201

@app.route('/api/cars', methods=['GET'])
@login_required
def get_cars():
    game_title_id = request.args.get('game_title_id')
    query = Car.query
    if game_title_id:
        query = query.filter_by(game_title_id=game_title_id)
    cars = query.all()
    return jsonify([{'id': car.id, 'name': car.name, 'game_title_id': car.game_title_id} for car in cars])

@app.route('/api/cars', methods=['POST'])
@login_required
def add_car():
    data = request.get_json()
    name = data.get('name')
    game_title_id = data.get('game_title_id')
    
    if not all([name, game_title_id]):
        return jsonify({'error': '車種名とゲームタイトルIDが必要です'}), 400
    
    if not GameTitle.query.get(game_title_id):
        return jsonify({'error': '指定されたゲームタイトルが存在しません'}), 400
    
    if Car.query.filter_by(name=name, game_title_id=game_title_id).first():
        return jsonify({'error': 'この車種は既に存在します'}), 400
    
    car = Car(name=name, game_title_id=game_title_id)
    db.session.add(car)
    db.session.commit()
    
    return jsonify({'id': car.id, 'name': car.name, 'game_title_id': car.game_title_id}), 201

@app.route('/api/courses', methods=['GET'])
@login_required
def get_courses():
    game_title_id = request.args.get('game_title_id')
    query = Course.query
    if game_title_id:
        query = query.filter_by(game_title_id=game_title_id)
    courses = query.all()
    return jsonify([{'id': course.id, 'name': course.name, 'game_title_id': course.game_title_id} for course in courses])

@app.route('/api/courses', methods=['POST'])
@login_required
def add_course():
    data = request.get_json()
    name = data.get('name')
    game_title_id = data.get('game_title_id')
    
    if not all([name, game_title_id]):
        return jsonify({'error': 'コース名とゲームタイトルIDが必要です'}), 400
    
    if not GameTitle.query.get(game_title_id):
        return jsonify({'error': '指定されたゲームタイトルが存在しません'}), 400
    
    if Course.query.filter_by(name=name, game_title_id=game_title_id).first():
        return jsonify({'error': 'このコースは既に存在します'}), 400
    
    course = Course(name=name, game_title_id=game_title_id)
    db.session.add(course)
    db.session.commit()
    
    return jsonify({'id': course.id, 'name': course.name, 'game_title_id': course.game_title_id}), 201

# データベースの初期化
with app.app_context():
    db.drop_all()  # 既存のテーブルを削除
    db.create_all()  # 新しいテーブルを作成

if __name__ == '__main__':
    app.run(debug=True, port=5004) 