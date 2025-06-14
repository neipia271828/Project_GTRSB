#!/bin/bash

# エラーが発生したら即座に終了
set -e

echo "GTRラップタイム記録アプリのセットアップを開始します..."

# 必要なディレクトリの作成
echo "ディレクトリを作成中..."
mkdir -p instance
mkdir -p static
mkdir -p templates

# Python仮想環境のセットアップ
if [ ! -d "venv" ]; then
    echo "Python仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境のアクティベート
echo "仮想環境をアクティベート中..."
source venv/bin/activate

# 依存関係のインストール
echo "依存関係をインストール中..."
pip install --upgrade pip
pip install -r requirements.txt

# データベースのリセット
echo "データベースをリセット中..."
rm -f instance/gtrsb.sqlite3
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# アプリケーションの起動
echo "アプリケーションを起動中..."
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
python3 app.py 

# エラーが発生したら即座に終了
set -e

echo "GTRラップタイム記録アプリのセットアップを開始します..."

# 必要なディレクトリの作成
echo "ディレクトリを作成中..."
mkdir -p instance
mkdir -p static
mkdir -p templates

# Python仮想環境のセットアップ
if [ ! -d "venv" ]; then
    echo "Python仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境のアクティベート
echo "仮想環境をアクティベート中..."
source venv/bin/activate

# 依存関係のインストール
echo "依存関係をインストール中..."
pip install -r requirements.txt

# データベースのリセット
rm -f ../instance/gtrsb.sqlite3
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# アプリケーションの起動
echo "アプリケーションを起動中..."
python3 app.py &
echo "アプリケーションが起動しました。http://localhost:5004 にアクセスしてください。" 