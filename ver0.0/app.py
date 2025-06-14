from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC, timedelta
import os
import hashlib
import re
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS
from functools import wraps
import jwt
from flask_migrate import Migrate

# アプリケーションのルートディレクトリを取得
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__,
           template_folder=os.path.join(BASE_DIR, 'templates'),
           static_folder=os.path.join(BASE_DIR, 'static'))
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 本番環境では環境変数から読み込むべき
app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']  # JWT用のシークレットキー
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gtrsb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORSの初期化
CORS(app)

# ロギングの設定
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('アプリケーション起動')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 診断結果を保持するグローバル変数
diagnostic_status = {
    'last_check': None,
    'database_status': 'unknown',
    'api_status': 'unknown',
    'error_count': 0
}

def run_diagnostic():
    """システムの診断を実行"""
    global diagnostic_status
    while True:
        try:
            with app.app_context():
                # データベース接続の確認
                db.session.execute(text('SELECT 1'))
                diagnostic_status['database_status'] = 'healthy'
                
                # APIの応答確認
                with app.test_client() as client:
                    response = client.get('/api/health')
                    if response.status_code == 200:
                        diagnostic_status['api_status'] = 'healthy'
                    else:
                        diagnostic_status['api_status'] = 'unhealthy'
                        diagnostic_status['error_count'] += 1
                
                diagnostic_status['last_check'] = datetime.now(UTC)
                app.logger.info(f'診断完了: {diagnostic_status}')
            
        except Exception as e:
            diagnostic_status['database_status'] = 'unhealthy'
            diagnostic_status['error_count'] += 1
            app.logger.error(f'診断エラー: {str(e)}')
        
        time.sleep(300)  # 5分ごとに診断

# データベースの初期化
with app.app_context():
    try:
        db.create_all()
        app.logger.info('データベースを初期化しました')
    except Exception as e:
        app.logger.error(f'データベース初期化エラー: {str(e)}')
        raise

# 診断スレッドの開始
diagnostic_thread = threading.Thread(target=run_diagnostic, daemon=True)
diagnostic_thread.start()

# データベースモデル
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    records = db.relationship('Record', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class GameTitle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    records = db.relationship('Record', backref='game_title', lazy=True)

class CarModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    records = db.relationship('Record', backref='car_model', lazy=True)

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    lap_count = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    records = db.relationship('Record', backref='track', lazy=True)

class Record(db.Model):
    """記録モデル"""
    id = db.Column(db.Integer, primary_key=True)
    game_title_id = db.Column(db.Integer, db.ForeignKey('game_title.id'), nullable=False)
    car_model_id = db.Column(db.Integer, db.ForeignKey('car_model.id'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)
    total_time = db.Column(db.Float, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    lap_times = db.relationship('LapTime', backref='record', lazy=True, cascade='all, delete-orphan')

    def __init__(self, game_title_id, car_model_id, track_id, total_time, created_by):
        self.game_title_id = game_title_id
        self.car_model_id = car_model_id
        self.track_id = track_id
        self.total_time = total_time
        self.created_by = created_by

class LapTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('record.id'), nullable=False)
    lap_number = db.Column(db.Integer, nullable=False)
    time = db.Column(db.String(20), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ユーティリティ関数
# 合計秒数(float)で返す

def calculate_total_time(lap_times):
    total_seconds = 0.0
    for time in lap_times:
        minutes, seconds = map(float, time.split(':'))
        total_seconds += minutes * 60 + seconds
    return total_seconds

# 表示用: 秒数(float)→MM:SS.mmm形式

def format_time(total_seconds):
    total_minutes = int(total_seconds // 60)
    remaining_seconds = total_seconds % 60
    return f"{total_minutes:02d}:{remaining_seconds:06.3f}"

# JWT認証用デコレーター
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'error': 'トークンが必要です'}), 401
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'ユーザーが存在しません'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'トークンの有効期限が切れています'}), 401
        except Exception as e:
            return jsonify({'error': 'トークンが無効です', 'detail': str(e)}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# ルート
@app.route('/')
def index():
    return render_template('index.html')

def validate_email(email):
    """メールアドレスのバリデーション"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password):
    """パスワードのバリデーション"""
    return len(password) >= 8

@app.route('/api/register', methods=['POST'])
def register():
    """ユーザー登録"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'メールアドレスとパスワードが必要です'}), 400
    
    if not validate_email(data['email']):
        return jsonify({'error': '無効なメールアドレス形式です'}), 400
    
    if not validate_password(data['password']):
        return jsonify({'error': 'パスワードは8文字以上必要です'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'このメールアドレスは既に登録されています'}), 400
    
    user = User(email=data['email'])
    user.set_password(data['password'])
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'ユーザー登録が完了しました'}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"ユーザー登録エラー: {str(e)}")
        return jsonify({'error': 'ユーザー登録に失敗しました'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        login_user(user)
        token = jwt.encode(
            {
                'user_id': user.id,
                'exp': datetime.now(UTC) + timedelta(days=1)  # トークンの有効期限を1日に設定
            },
            app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        return jsonify({
            'id': user.id,
            'email': user.email,
            'token': token
        })
    return jsonify({'error': 'メールアドレスまたはパスワードが正しくありません'}), 401

@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'ログアウトしました'})

# ゲームタイトルAPI
@app.route('/api/game-titles', methods=['GET'])
@token_required
def get_game_titles(current_user):
    game_titles = GameTitle.query.all()
    return jsonify([{
        'id': gt.id,
        'name': gt.name
    } for gt in game_titles])

@app.route('/api/game-titles', methods=['POST'])
@token_required
def create_game_title(current_user):
    """ゲームタイトルの作成"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'ゲームタイトル名が必要です'}), 400
    
    # 重複チェック
    if GameTitle.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'このゲームタイトルは既に存在します'}), 400
    
    game_title = GameTitle(name=data['name'], created_by=current_user.id)
    
    try:
        db.session.add(game_title)
        db.session.commit()
        return jsonify({
            'message': 'ゲームタイトルが作成されました',
            'game_title_id': game_title.id
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"ゲームタイトル作成エラー: {str(e)}")
        return jsonify({'error': 'ゲームタイトルの作成に失敗しました'}), 500

# 車種API
@app.route('/api/car-models', methods=['GET'])
@token_required
def get_car_models(current_user):
    car_models = CarModel.query.all()
    return jsonify([{
        'id': cm.id,
        'name': cm.name
    } for cm in car_models])

@app.route('/api/car-models', methods=['POST'])
@token_required
def add_car_model(current_user):
    data = request.get_json()
    if CarModel.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'この車種は既に登録されています'}), 400
    
    car_model = CarModel(
        name=data['name'],
        created_by=current_user.id
    )
    db.session.add(car_model)
    db.session.commit()
    return jsonify({
        'id': car_model.id,
        'name': car_model.name
    }), 201

# コースAPI
@app.route('/api/tracks', methods=['GET'])
@token_required
def get_tracks(current_user):
    tracks = Track.query.all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'lap_count': t.lap_count
    } for t in tracks])

@app.route('/api/tracks', methods=['POST'])
@token_required
def add_track(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'コース名が必要です'}), 400
    if Track.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'このコースは既に登録されています'}), 400
    if not isinstance(data.get('lap_count'), int) or data['lap_count'] < 1:
        return jsonify({'error': 'ラップ数は1以上の整数を指定してください'}), 400
    track = Track(
        name=data['name'],
        lap_count=data['lap_count'],
        created_by=current_user.id
    )
    db.session.add(track)
    db.session.commit()
    return jsonify({
        'id': track.id,
        'name': track.name,
        'lap_count': track.lap_count
    }), 201

# 記録API
@app.route('/api/records', methods=['GET'])
@token_required
def get_records(current_user):
    filters = {}
    if request.args.get('game_title_id'):
        filters['game_title_id'] = request.args.get('game_title_id')
    if request.args.get('car_model_id'):
        filters['car_model_id'] = request.args.get('car_model_id')
    if request.args.get('track_id'):
        filters['track_id'] = request.args.get('track_id')
    if request.args.get('user_id'):
        # Recordモデルでは作成者をcreated_byで管理しているため
        # クエリパラメータuser_idはcreated_byにマッピングする
        filters['created_by'] = request.args.get('user_id')
    
    records = Record.query.filter_by(**filters).order_by(Record.total_time).all()
    return jsonify([{
        'id': r.id,
        'user': r.user.email,
        'game_title': r.game_title.name,
        'car_model': r.car_model.name,
        'track': r.track.name,
        'total_time': format_time(r.total_time),
        'lap_times': [{
            'lap_number': lt.lap_number,
            'time': lt.time
        } for lt in r.lap_times],
        'comment': getattr(r, 'comment', None),
        'created_at': r.created_at.isoformat()
    } for r in records])

@app.route('/api/records', methods=['POST'])
@token_required
def add_record(current_user):
    data = request.get_json()
    
    # バリデーション
    if not all(key in data for key in ['game_title_id', 'car_model_id', 'track_id', 'lap_times']):
        return jsonify({'error': '必要な情報が不足しています'}), 400
    
    track = Track.query.get(data['track_id'])
    if not track:
        return jsonify({'error': '指定されたコースが見つかりません'}), 404
    
    if len(data['lap_times']) != track.lap_count:
        return jsonify({'error': f'ラップタイムの数が正しくありません（{track.lap_count}周のコースです）'}), 400
    
    # ラップタイムのバリデーション
    for time in data['lap_times']:
        if not re.match(r'^\d{2}:\d{2}\.\d{3}$', time):
            return jsonify({'error': 'ラップタイムの形式が正しくありません（MM:SS.mmm）'}), 400
    
    # 全体タイムの計算
    total_time = calculate_total_time(data['lap_times'])
    
    # 記録の作成
    record = Record(
        game_title_id=data['game_title_id'],
        car_model_id=data['car_model_id'],
        track_id=data['track_id'],
        total_time=total_time,
        created_by=current_user.id
    )
    db.session.add(record)
    db.session.flush()  # IDを生成
    
    # ラップタイムの作成
    for i, time in enumerate(data['lap_times'], 1):
        lap_time = LapTime(
            record_id=record.id,
            lap_number=i,
            time=time
        )
        db.session.add(lap_time)
    
    db.session.commit()
    return jsonify({
        'id': record.id,
        'total_time': format_time(record.total_time),
        'created_at': record.created_at.isoformat()
    }), 201

@app.route('/api/health', methods=['GET'])
def health_check():
    """システムの健全性を確認"""
    try:
        # データベース接続の確認
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(UTC).isoformat(),
            'database': 'connected',
            'api': 'running'
        }), 200
    except Exception as e:
        app.logger.error(f'ヘルスチェックエラー: {str(e)}')
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(UTC).isoformat()
        }), 500

@app.route('/api/diagnostic', methods=['GET'])
def get_diagnostic():
    """診断結果を取得するエンドポイント"""
    if 'user_id' not in session:
        return jsonify({'error': 'ログインが必要です'}), 401
    
    return jsonify({
        'last_check': diagnostic_status['last_check'].isoformat() if diagnostic_status['last_check'] else None,
        'database_status': diagnostic_status['database_status'],
        'api_status': diagnostic_status['api_status'],
        'error_count': diagnostic_status['error_count']
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("DB初期化完了")
    app.run(host='127.0.0.1', port=5001, debug=True) 