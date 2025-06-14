// ユーザー情報の表示
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/user');
        if (!response.ok) {
            throw new Error('認証エラー');
        }
        const data = await response.json();
        document.getElementById('username').textContent = data.username;
    } catch (error) {
        window.location.href = '/';
    }
});

// ログアウト処理
document.getElementById('logout-btn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/logout', { method: 'POST' });
        if (response.ok) {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('ログアウトエラー:', error);
    }
});

// フォームのリセット
function resetForm() {
    document.getElementById('lap-form').reset();
    document.getElementById('lap-id').value = '';
    document.getElementById('submit-btn').textContent = '記録';
    document.getElementById('cancel-btn').style.display = 'none';
}

// キャンセルボタンの処理
document.getElementById('cancel-btn').addEventListener('click', resetForm);

// ラップタイム記録フォームの処理
document.getElementById('lap-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const lapId = formData.get('lap_id');
    const data = {
        game_title: formData.get('game_title'),
        car_model: formData.get('car_model'),
        track_name: formData.get('track_name'),
        lap_time: formData.get('lap_time'),
        notes: formData.get('notes')
    };

    try {
        const url = lapId ? `/api/laps/${lapId}` : '/api/laps';
        const method = lapId ? 'PUT' : 'POST';
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('記録に失敗しました');
        }

        // フォームをリセット
        resetForm();
        // ラップタイム一覧を更新
        loadRecentLaps();
    } catch (error) {
        alert(error.message);
    }
});

// ラップタイムの編集
async function editLap(lapId) {
    try {
        const response = await fetch(`/api/laps/${lapId}`);
        if (!response.ok) {
            throw new Error('データの取得に失敗しました');
        }
        const lap = await response.json();
        
        // フォームに値を設定
        document.getElementById('lap-id').value = lap.id;
        document.getElementById('game-title').value = lap.game_title;
        document.getElementById('car-model').value = lap.car_model;
        document.getElementById('track-name').value = lap.track_name;
        document.getElementById('lap-time').value = lap.lap_time;
        document.getElementById('notes').value = lap.notes || '';
        
        // ボタンの表示を変更
        document.getElementById('submit-btn').textContent = '更新';
        document.getElementById('cancel-btn').style.display = 'block';
        
        // フォームまでスクロール
        document.querySelector('.record-form').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        alert(error.message);
    }
}

// ラップタイムの削除
async function deleteLap(lapId) {
    if (!confirm('このラップタイムを削除してもよろしいですか？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/laps/${lapId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('削除に失敗しました');
        }
        
        // ラップタイム一覧を更新
        loadRecentLaps();
    } catch (error) {
        alert(error.message);
    }
}

// 最近のラップタイム一覧の読み込み
async function loadRecentLaps() {
    try {
        const response = await fetch('/api/laps');
        if (!response.ok) {
            throw new Error('データの取得に失敗しました');
        }
        const laps = await response.json();
        const lapsList = document.getElementById('laps-list');
        lapsList.innerHTML = laps.map(lap => `
            <div class="lap-item">
                <h3>${lap.game_title}</h3>
                <div class="lap-actions">
                    <button class="edit-btn" onclick="editLap(${lap.id})">編集</button>
                    <button class="delete-btn" onclick="deleteLap(${lap.id})">削除</button>
                </div>
                <p>車種: ${lap.car_model}</p>
                <p>コース: ${lap.track_name}</p>
                <p>タイム: ${lap.lap_time}</p>
                ${lap.notes ? `<p>備考: ${lap.notes}</p>` : ''}
                <p>記録日時: ${new Date(lap.recorded_at).toLocaleString()}</p>
            </div>
        `).join('');
    } catch (error) {
        console.error('ラップタイム一覧の読み込みエラー:', error);
    }
}

// 初期表示時にラップタイム一覧を読み込む
loadRecentLaps(); 