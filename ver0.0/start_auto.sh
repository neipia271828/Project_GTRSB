#!/bin/bash

cd "$(dirname "$0")"

# ポート5001を使用しているプロセスを取得
PID=$(lsof -ti :5001)

if [ ! -z "$PID" ]; then
  echo "ポート5001を使用しているプロセス($PID)を強制終了します..."
  kill -9 $PID
  sleep 1
else
  echo "ポート5001は使用されていません。"
fi

echo "アプリケーションを起動します..."
./start.sh 