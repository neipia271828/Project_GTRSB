from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import hashlib
import re
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
                
                diagnostic_status['last_check'] = datetime.utcnow()
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
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kamiyama_id_hash = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class GameTitle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('game_titles', lazy=True))

class CarModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('car_models', lazy=True))

class TrackName(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    lap_count = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('track_names', lazy=True))

class Lap(db.Model):
    __tablename__ = 'lap'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_title_id = db.Column(db.Integer, db.ForeignKey('game_title.id'), nullable=False)
    car_model_id = db.Column(db.Integer, db.ForeignKey('car_model.id'), nullable=False)
    track_name_id = db.Column(db.Integer, db.ForeignKey('track_name.id'), nullable=False)
    total_time = db.Column(db.String(10), nullable=False)
    lap_count = db.Column(db.Integer, nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # リレーションシップ
    user = db.relationship('User', backref=db.backref('laps', lazy=True))
    game_title = db.relationship('GameTitle', backref=db.backref('laps', lazy=True))
    car_model = db.relationship('CarModel', backref=db.backref('laps', lazy=True))
    track_name = db.relationship('TrackName', backref=db.backref('track_laps', lazy=True))
    lap_times = db.relationship('LapTime', backref=db.backref('parent_lap', lazy=True), cascade='all, delete-orphan')

class LapTime(db.Model):
    __tablename__ = 'lap_time'
    id = db.Column(db.Integer, primary_key=True)
    lap_id = db.Column(db.Integer, db.ForeignKey('lap.id'), nullable=False)
    lap_number = db.Column(db.Integer, nullable=False)
    time = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# メールアドレス検証用の正規表現
KAMIYAMA_EMAIL_PATTERN = r'^kmc\d{4}@kamiyama\.ac\.jp$'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_kamiyama_email(email):
    return bool(re.match(KAMIYAMA_EMAIL_PATTERN, email))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'メールアドレスとパスワードは必須です'}), 400
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'error': '有効なメールアドレスを入力してください'}), 400
    
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    
    if User.query.filter_by(kamiyama_id_hash=email_hash).first():
        return jsonify({'error': 'このメールアドレスは既に登録されています'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    new_user = User(
        kamiyama_id_hash=email_hash
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': '登録が完了しました'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'メールアドレスとパスワードは必須です'}), 400
    
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    user = User.query.filter_by(kamiyama_id_hash=email_hash).first()
    
    if not user:
        return jsonify({'error': 'メールアドレスまたはパスワードが正しくありません'}), 401
    
    session['user_id'] = user.id
    return jsonify({'message': 'ログインしました'}), 200

@app.route('/api/game-titles', methods=['GET'])
def get_game_titles():
    titles = GameTitle.query.order_by(GameTitle.name).all()
    return jsonify([{'id': title.id, 'name': title.name} for title in titles])

@app.route('/api/car-models', methods=['GET'])
def get_car_models():
    models = CarModel.query.order_by(CarModel.name).all()
    return jsonify([{'id': model.id, 'name': model.name} for model in models])

@app.route('/api/track-names', methods=['GET'])
def get_track_names():
    if 'user_id' not in session:
        return jsonify({'error': 'ログインが必要です'}), 401
    
    tracks = TrackName.query.all()
    return jsonify([{
        'id': track.id,
        'name': track.name,
        'lap_count': track.lap_count
    } for track in tracks])

@app.route('/api/game-titles', methods=['POST'])
def add_game_title():
    if 'user_id' not in session:
        return jsonify({'error': 'ログインが必要です'}), 401

    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': 'ゲームタイトルを入力してください'}), 400

    if GameTitle.query.filter_by(name=name).first():
        return jsonify({'error': 'このゲームタイトルは既に登録されています'}), 400

    new_title = GameTitle(
        name=name,
        created_by=session['user_id']
    )

    db.session.add(new_title)
    db.session.commit()

    return jsonify({'id': new_title.id, 'name': new_title.name}), 201

@app.route('/api/car-models', methods=['POST'])
def add_car_model():
    if 'user_id' not in session:
        return jsonify({'error': 'ログインが必要です'}), 401

    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': '車種を入力してください'}), 400

    if CarModel.query.filter_by(name=name).first():
        return jsonify({'error': 'この車種は既に登録されています'}), 400

    new_model = CarModel(
        name=name,
        created_by=session['user_id']
    )

    db.session.add(new_model)
    db.session.commit()

    return jsonify({'id': new_model.id, 'name': new_model.name}), 201

@app.route('/api/track-names', methods=['POST'])
def add_track_name():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'ログインが必要です'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'リクエストデータが不正です'}), 400

        name = data.get('name')
        lap_count = data.get('lap_count', 1)

        if not name or not isinstance(name, str) or len(name.strip()) == 0:
            return jsonify({'error': 'コース名は必須です'}), 400

        if not isinstance(lap_count, int) or lap_count < 1:
            return jsonify({'error': 'ラップ数は1以上の整数を指定してください'}), 400

        # 既存のコース名をチェック（大文字小文字を区別しない）
        existing_track = TrackName.query.filter(
            db.func.lower(TrackName.name) == db.func.lower(name)
        ).first()
        
        if existing_track:
            return jsonify({'error': 'このコース名は既に登録されています'}), 400

        new_track = TrackName(
            name=name.strip(),
            lap_count=lap_count,
            created_by=session['user_id']
        )
        db.session.add(new_track)
        db.session.commit()

        return jsonify({
            'message': 'コースを登録しました',
            'track': {
                'id': new_track.id,
                'name': new_track.name,
                'lap_count': new_track.lap_count
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'コース登録エラー: {str(e)}')
        return jsonify({'error': 'コースの登録に失敗しました'}), 500

@app.route('/api/laps', methods=['POST'])
def add_lap():
    if 'user_id' not in session:
        return jsonify({'error': 'ログインが必要です'}), 401
    
    data = request.get_json()
    
    # 必須フィールドの確認
    required_fields = ['game_title_id', 'car_model_id', 'track_name_id', 'lap_times']
    if not all(field in data for field in required_fields):
        return jsonify({'error': '必須フィールドが不足しています'}), 400
    
    try:
        # ラップタイムの合計を計算
        total_seconds = 0
        lap_times = data['lap_times']
        # lap_timesがdictのリストかstrのリストか判定
        if isinstance(lap_times[0], dict):
            lap_time_strs = [lt['time'] for lt in lap_times]
        else:
            lap_time_strs = lap_times
        for lap_time in lap_time_strs:
            minutes, seconds = map(float, lap_time.split(':'))
            total_seconds += minutes * 60 + seconds
        total_minutes = int(total_seconds // 60)
        total_seconds = total_seconds % 60
        total_time = f"{total_minutes:02d}:{total_seconds:06.3f}"
        
        # 新しいラップ記録を作成
        lap = Lap(
            user_id=session['user_id'],
            game_title_id=data['game_title_id'],
            car_model_id=data['car_model_id'],
            track_name_id=data['track_name_id'],
            total_time=total_time,
            lap_count=len(lap_time_strs),
            note=data.get('note', '')
        )
        db.session.add(lap)
        db.session.flush()  # IDを生成するためにflush
        
        # 各ラップの時間を記録
        for i, lap_time in enumerate(lap_time_strs, 1):
            lap_time_record = LapTime(
                lap_id=lap.id,
                lap_number=i,
                time=lap_time
            )
            db.session.add(lap_time_record)
        
        db.session.commit()
        return jsonify({'message': 'ラップタイムが記録されました'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/laps', methods=['GET'])
def get_laps():
    if 'user_id' not in session:
        return jsonify({'error': 'ログインが必要です'}), 401
    
    game_title_id = request.args.get('game_title_id', type=int)
    car_model_id = request.args.get('car_model_id', type=int)
    track_name_id = request.args.get('track_name_id', type=int)
    
    query = Lap.query.filter_by(user_id=session['user_id'])
    
    if game_title_id:
        query = query.filter_by(game_title_id=game_title_id)
    if car_model_id:
        query = query.filter_by(car_model_id=car_model_id)
    if track_name_id:
        query = query.filter_by(track_name_id=track_name_id)
    
    laps = query.order_by(Lap.created_at.desc()).all()
    
    return jsonify([{
        'id': lap.id,
        'game_title': lap.game_title.name,
        'car_model': lap.car_model.name,
        'track_name': lap.track_name.name,
        'total_time': lap.total_time,
        'lap_count': lap.lap_count,
        'lap_times': [{
            'lap_number': lt.lap_number,
            'time': lt.time
        } for lt in lap.lap_times],
        'note': lap.note,
        'created_at': lap.created_at.isoformat()
    } for lap in laps])

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    game_title_id = request.args.get('game_title_id')
    car_model_id = request.args.get('car_model_id')
    track_name_id = request.args.get('track_name_id')

    if not all([game_title_id, car_model_id, track_name_id]):
        return jsonify({'error': 'ゲームタイトル、車種、コースを選択してください'}), 400

    query = Lap.query.filter_by(
        game_title_id=game_title_id,
        car_model_id=car_model_id,
        track_name_id=track_name_id
    ).join(User).order_by(Lap.lap_time)

    laps = query.all()
    
    return jsonify([{
        'username': lap.user.username,
        'lap_time': lap.lap_time,
        'recorded_at': lap.recorded_at.isoformat(),
        'notes': lap.notes
    } for lap in laps])

@app.route('/api/health', methods=['GET'])
def health_check():
    """システムの健全性を確認"""
    try:
        # データベース接続の確認
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'api': 'running'
        }), 200
    except Exception as e:
        app.logger.error(f'ヘルスチェックエラー: {str(e)}')
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
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