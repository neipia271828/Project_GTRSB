document.addEventListener('DOMContentLoaded', function() {
    // タブ切り替え
    const tabs = document.querySelectorAll('.auth-tab');
    const forms = document.querySelectorAll('.auth-form');
    
    if (tabs.length > 0 && forms.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.getAttribute('data-target');
                tabs.forEach(t => t.classList.remove('active'));
                forms.forEach(f => f.style.display = 'none');
                tab.classList.add('active');
                document.getElementById(target).style.display = 'block';
            });
        });
    }

    // ログインフォーム
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
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

                if (response.ok) {
                    window.location.href = '/dashboard';
                } else {
                    const data = await response.json();
                    alert(data.error || 'ログインに失敗しました');
                }
            } catch (error) {
                alert('ログインに失敗しました');
            }
        });
    }

    // 新規登録フォーム
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const username = document.getElementById('register-username').value;

            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, password, username })
                });

                if (response.ok) {
                    alert('登録が完了しました。ログインしてください。');
                    // ログインフォームに切り替え
                    document.querySelector('[data-target="login-form"]').click();
                    registerForm.reset();
                } else {
                    const data = await response.json();
                    alert(data.error || '登録に失敗しました');
                }
            } catch (error) {
                alert('登録に失敗しました');
            }
        });
    }
});

document.getElementById('auth-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const email = this.email.value.trim();
    const password = this.password.value.trim();
    const username = this.username.value.trim();
    const message = document.getElementById('message');
    message.textContent = '';

    // メールアドレス形式チェック
    if (!/^kmc\d{4}@kamiyama\.ac\.jp$/.test(email)) {
        message.textContent = 'メールアドレス形式が正しくありません。';
        return;
    }
    // パスワード4桁チェック
    if (!/^\d{4}$/.test(password)) {
        message.textContent = 'パスワードは4桁の数字で入力してください。';
        return;
    }

    try {
        const isRegister = username.length > 0;
        const endpoint = isRegister ? '/api/register' : '/api/login';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
                username
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'エラーが発生しました。');
        }

        message.textContent = data.message;
        message.style.color = '#2ecc40';
        
        // 成功時のリダイレクト（後で実装）
        // window.location.href = '/dashboard';
        
    } catch (error) {
        message.textContent = error.message;
        message.style.color = '#ff6666';
    }
});

document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const username = document.getElementById('register-username').value;

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password, username })
        });

        const data = await response.json();
        if (response.ok) {
            alert(data.message);
            window.location.href = data.redirect;
        } else {
            alert(data.error);
        }
    } catch (error) {
        alert('エラーが発生しました。');
    }
}); 