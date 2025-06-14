#!/bin/bash

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境が存在しない場合は作成
if [ ! -d "venv" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    # 仮想環境を有効化
    source venv/bin/activate
fi

# アプリケーションを起動
echo "アプリケーションを起動しています..."
echo "ブラウザで http://127.0.0.1:5001 にアクセスしてください"
echo "終了するには Ctrl+C を押してください"
python app.py 

# ポート5001を使用しているプロセスを特定
PID=$(lsof -i :5001 | awk 'NR>1 {print $2}')

# 該当プロセスを強制終了
kill -9 $PID 

# 再度アプリを起動
./start.sh 