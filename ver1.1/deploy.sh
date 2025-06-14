#!/bin/bash

# エラーが発生したら即座に終了
set -e

echo "GTRラップタイム記録アプリのデプロイを開始します..."

# サーバー情報
SERVER="gtrsb@133.125.84.34"
REMOTE_DIR="/home/gtrsb/gtrsb"
SSH_KEY="$HOME/.ssh/gtrsb_key"

# SSHオプション
SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=no"

# サーバー上で実行するコマンド
echo "サーバー上のプロセスを停止中..."
ssh $SSH_OPTS $SERVER "cd $REMOTE_DIR && pkill -f 'python.*app.py' || true"

echo "サーバー上の環境をクリーンアップ中..."
ssh $SSH_OPTS $SERVER "cd $REMOTE_DIR && \
    rm -rf venv && \
    rm -f instance/gtrsb.sqlite3 && \
    mkdir -p instance static templates"

echo "ファイルをアップロード中..."
scp -i $SSH_KEY -r * $SERVER:$REMOTE_DIR/

echo "サーバー上でアプリケーションを起動中..."
ssh $SSH_OPTS $SERVER "cd $REMOTE_DIR && \
    chmod +x run.sh && \
    ./run.sh"

echo "デプロイが完了しました。"
echo "アプリケーションは https://gtrsb.com でアクセス可能です。" 