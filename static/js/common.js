/* EAMS 公共前端工具：统一请求、消息提示与安全文本处理 */

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function toast(message, type = 'success') {
    let area = document.getElementById('toastArea');
    if (!area) {
        area = document.createElement('div');
        area.id = 'toastArea';
        area.className = 'toast-area';
        document.body.appendChild(area);
    }
    const item = document.createElement('div');
    item.className = `toast toast-${type}`;
    item.textContent = message;
    area.appendChild(item);
    requestAnimationFrame(() => item.classList.add('show'));
    setTimeout(() => {
        item.classList.remove('show');
        setTimeout(() => item.remove(), 220);
    }, 2600);
}

async function api(url, method = 'GET', body = null, options = {}) {
    const request = { method, headers: { Accept: 'application/json' } };
    if (body !== null && body !== undefined) {
        request.headers['Content-Type'] = 'application/json';
        request.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(url, request);
        const contentType = response.headers.get('content-type') || '';
        const json = contentType.includes('application/json')
            ? await response.json()
            : { code: response.status, msg: await response.text(), data: null };

        if (response.ok && json.code === 0) return json.data;

        let message = json.msg || json.detail || `请求失败（HTTP ${response.status}）`;
        if (Array.isArray(json.data)) {
            const first = json.data[0];
            if (first?.msg) message += `：${first.msg}`;
        }
        throw new Error(message);
    } catch (error) {
        const message = error instanceof TypeError
            ? '无法连接后端，请确认 FastAPI 和 MySQL 已启动'
            : error.message;
        if (!options.silent) toast(message, 'error');
        throw error;
    }
}

async function apiSafe(url, fallback = null) {
    try {
        return await api(url, 'GET', null, { silent: true });
    } catch (_) {
        return fallback;
    }
}

function logout() {
    localStorage.clear();
    location.href = '/static/login.html';
}
