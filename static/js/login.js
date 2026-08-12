async function login() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const message = document.getElementById('msg');
    if (!username || !password) return toast('请输入用户名和密码', 'error');

    try {
        const data = await api('/auth/login', 'POST', { username, password });
        localStorage.setItem('username', data.username);
        localStorage.setItem('role', data.role);
        localStorage.setItem('user_id', data.id);
        message.className = 'msg success';
        message.textContent = '登录成功，正在进入管理中心…';
        setTimeout(() => location.href = '/static/dashboard.html', 450);
    } catch (error) {
        message.className = 'msg error';
        message.textContent = error.message;
    }
}

document.addEventListener('keydown', event => {
    if (event.key === 'Enter') login();
});
