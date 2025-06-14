// グローバル変数
let currentUser = null;
let token = null;

// DOMの読み込み完了時に実行
document.addEventListener('DOMContentLoaded', () => {
    // フォームのイベントリスナーを設定
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    document.getElementById('record-form').addEventListener('submit', handleRecordSubmit);

    // 初期データの読み込み
    loadGameTitles();
    loadCarModels();
    loadTracks();
    loadRecords();
});

// ログイン処理
async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        if (response.ok) {
            currentUser = data;
            token = data.token;
            showAuthenticatedUI();
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('ログインに失敗しました');
    }
}

// 登録処理
async function handleRegister(event) {
    event.preventDefault();
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        if (response.ok) {
            alert('登録が完了しました');
            document.getElementById('register-form').reset();
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('登録に失敗しました');
    }
}

// 記録の送信処理
async function handleRecordSubmit(event) {
    event.preventDefault();
    if (!token) {
        alert('ログインが必要です');
        return;
    }

    const gameTitleId = document.getElementById('game-title').value;
    const trackId = document.getElementById('track').value;
    const carModelId = document.getElementById('car-model').value;
    const comment = document.getElementById('comment').value;

    const lapTimes = [];
    const lapTimeInputs = document.querySelectorAll('.lap-time-input input');
    lapTimeInputs.forEach((input, index) => {
        lapTimes.push({
            lap_number: index + 1,
            time: input.value
        });
    });

    try {
        const response = await fetch('/api/records', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                game_title_id: gameTitleId,
                track_id: trackId,
                car_model_id: carModelId,
                lap_times: lapTimes,
                comment: comment
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert('記録を保存しました');
            document.getElementById('record-form').reset();
            loadRecords();
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Record submission error:', error);
        alert('記録の保存に失敗しました');
    }
}

// 認証済みUIの表示
function showAuthenticatedUI() {
    document.getElementById('auth-section').style.display = 'none';
    document.getElementById('record-section').style.display = 'block';
    document.getElementById('leaderboard-section').style.display = 'block';
}

// データの読み込み関数
async function loadGameTitles() {
    try {
        const response = await fetch('/api/game-titles', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        updateSelectOptions('game-title', data);
        updateSelectOptions('filter-game-title', data);
    } catch (error) {
        console.error('Error loading game titles:', error);
    }
}

async function loadCarModels() {
    try {
        const response = await fetch('/api/car-models', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        updateSelectOptions('car-model', data);
        updateSelectOptions('filter-car-model', data);
    } catch (error) {
        console.error('Error loading car models:', error);
    }
}

async function loadTracks() {
    try {
        const response = await fetch('/api/tracks', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        updateSelectOptions('track', data);
        updateSelectOptions('filter-track', data);
    } catch (error) {
        console.error('Error loading tracks:', error);
    }
}

async function loadRecords() {
    try {
        const response = await fetch('/api/records', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        updateLeaderboard(data);
    } catch (error) {
        console.error('Error loading records:', error);
    }
}

// セレクトボックスの更新
function updateSelectOptions(selectId, data) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">選択してください</option>';
    data.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name;
        select.appendChild(option);
    });
}

// リーダーボードの更新
function updateLeaderboard(records) {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '';
    
    records.forEach((record, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${record.user}</td>
            <td>${record.game_title}</td>
            <td>${record.track}</td>
            <td>${record.car_model}</td>
            <td>${record.total_time}</td>
            <td>${record.lap_times.map(lt => lt.time).join(', ')}</td>
            <td>${record.comment || ''}</td>
            <td>${new Date(record.created_at).toLocaleString()}</td>
        `;
        tbody.appendChild(row);
    });
} 