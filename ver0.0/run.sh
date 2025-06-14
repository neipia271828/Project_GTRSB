#!/bin/bash

# エラーが発生したら即座に終了
set -e

# カレントディレクトリをスクリプトの場所に移動
cd "$(dirname "$0")"

echo "=== GTRSB アプリケーション起動スクリプト ==="

# 仮想環境の確認と作成
if [ ! -d "venv" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv venv
fi

# 仮想環境のアクティベート
echo "仮想環境をアクティベートしています..."
source venv/bin/activate

# 必要なパッケージのインストール
echo "必要なパッケージをインストールしています..."
pip install -r requirements.txt

# データベースファイルの削除（存在する場合）
echo "データベースを初期化しています..."
rm -f instance/app.db app.db

# ポート5001を使用しているプロセスの確認と終了
echo "ポート5001の状態を確認しています..."
PID=$(lsof -ti :5001 || true)
if [ ! -z "$PID" ]; then
    echo "ポート5001を使用しているプロセス($PID)を終了します..."
    kill -9 $PID
    sleep 1
fi

# ログディレクトリの作成
echo "ログディレクトリを作成しています..."
mkdir -p logs

# アプリケーションの起動
echo "アプリケーションを起動しています..."
echo "ブラウザで http://127.0.0.1:5001 にアクセスしてください"
echo "終了するには Ctrl+C を押してください"
echo "=========================================="

# アプリケーションの実行
python3 app.py

# 仮想環境のデアクティベート
deactivate 