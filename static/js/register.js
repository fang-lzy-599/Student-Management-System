async function register() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const name = document.getElementById('name').value.trim();
    const gender = document.getElementById('gender').value;
    const ageText = document.getElementById('age').value;
    const age = Number(ageText);
    const message = document.getElementById('msg');

    if (username.length < 3 || username.length > 20) return toast('用户名需为 3 到 20 位', 'error');
    if (password.length < 6 || password.length > 20) return toast('密码需为 6 到 20 位', 'error');
    if (!name) return toast('请输入真实姓名', 'error');
    if (!ageText || age < 10 || age > 100) return toast('年龄必须在 10 到 100 之间', 'error');

    try {
        await api('/auth/register', 'POST', { username, password, name, gender, age });
        message.className = 'msg success';
        message.textContent = '注册成功，即将返回登录页…';
        setTimeout(() => location.href = '/static/login.html', 700);
    } catch (error) {
        message.className = 'msg error';
        message.textContent = error.message;
    }
}

document.addEventListener('keydown', event => {
    if (event.key === 'Enter') register();
});
