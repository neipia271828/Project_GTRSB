import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app, db, User, GameTitle, CarModel, TrackName, Lap, LapTime
import hashlib
from datetime import datetime

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(client, email, password, username):
    return client.post('/api/register', json={
        'email': email,
        'password': password,
        'username': username
    })

def login_user(client, email, password):
    return client.post('/api/login', json={
        'email': email,
        'password': password
    })

def add_game_title(client, name):
    return client.post('/api/game-titles', json={'name': name})

def test_register_user(client):
    """ユーザー登録のテスト"""
    response = client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    assert b'\u767b\u9332\u304c\u5b8c\u4e86\u3057\u307e\u3057\u305f' in response.data

def test_login_user(client):
    """ユーザーログインのテスト"""
    # まずユーザーを登録
    client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # ログインを試行
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    assert b'\u30ed\u30b0\u30a4\u30f3\u3057\u307e\u3057\u305f' in response.data

def test_add_game_title(client):
    """ゲームタイトル追加のテスト"""
    # まずログイン
    client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # ゲームタイトルを追加
    response = client.post('/api/game-titles', json={
        'name': 'Gran Turismo 7'
    })
    assert response.status_code == 201
    assert b'Gran Turismo 7' in response.data

def test_add_track_name(client):
    """コース追加のテスト"""
    # まずログイン
    client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # コースを追加
    response = client.post('/api/track-names', json={
        'name': 'Suzuka Circuit',
        'lap_count': 3
    })
    assert response.status_code == 201
    assert b'Suzuka Circuit' in response.data

def test_add_lap(client):
    """ラップタイム記録のテスト"""
    # まずユーザー登録・ログイン
    client.post('/api/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    # ユーザーID取得
    user = User.query.filter_by(kamiyama_id_hash=hashlib.sha256('test@example.com'.encode()).hexdigest()).first()
    # 必要なデータを追加
    game_title = GameTitle(name='Gran Turismo 7', created_by=user.id)
    car_model = CarModel(name='Nissan GT-R', created_by=user.id)
    track_name = TrackName(name='Suzuka Circuit', lap_count=3, created_by=user.id)
    db.session.add_all([game_title, car_model, track_name])
    db.session.commit()
    
    # ラップタイムを記録
    response = client.post('/api/laps', json={
        'game_title_id': game_title.id,
        'car_model_id': car_model.id,
        'track_name_id': track_name.id,
        'lap_times': [
            {'lap_number': 1, 'time': '1:30.000'},
            {'lap_number': 2, 'time': '1:29.500'},
            {'lap_number': 3, 'time': '1:29.000'}
        ],
        'note': 'テスト走行'
    })
    print('レスポンス:', response.status_code, response.data)
    assert response.status_code == 201
    # 日本語メッセージでアサート
    assert b'\u30e9\u30c3\u30d7\u30bf\u30a4\u30e0\u304c\u8a18\u9332\u3055\u308c\u307e\u3057\u305f' in response.data

def test_health_check(client):
    """ヘルスチェックのテスト"""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert b'healthy' in response.data 