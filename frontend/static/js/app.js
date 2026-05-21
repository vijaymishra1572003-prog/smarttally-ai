/* SmartTally AI - Main Application JavaScript */

// API Helper
async function fetchAPI(url, options = {}) {
    const token = localStorage.getItem('access_token');
    const defaultHeaders = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };

    if (options.body instanceof FormData) {
        delete defaultHeaders['Content-Type'];
    }

    const response = await fetch(url, {
        ...options,
        headers: { ...defaultHeaders, ...options.headers },
    });

    if (response.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
            return fetchAPI(url, options);
        }
        localStorage.clear();
        window.location.href = '/login';
        throw new Error('Session expired');
    }

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || 'API Error');
    }
    return data;
}

// Token Refresh
async function refreshToken() {
    const refreshTk = localStorage.getItem('refresh_token');
    if (!refreshTk) return false;

    try {
        const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${refreshTk}`,
                'Content-Type': 'application/json',
            },
        });
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            return true;
        }
    } catch (e) {
        console.error('Token refresh failed');
    }
    return false;
}

// Toast Notifications
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: '<i class="bi bi-check-circle-fill text-success fs-5"></i>',
        error: '<i class="bi bi-x-circle-fill text-danger fs-5"></i>',
        warning: '<i class="bi bi-exclamation-triangle-fill text-warning fs-5"></i>',
        info: '<i class="bi bi-info-circle-fill text-primary fs-5"></i>',
    };

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `${icons[type] || icons.info}<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Theme Toggle
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
}

// Load saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// Logout
function logout() {
    localStorage.clear();
    window.location.href = '/login';
}

// Load user info in sidebar
function loadUserInfo() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const avatar = document.getElementById('userAvatar');
    const name = document.getElementById('userName');
    const role = document.getElementById('userRole');

    if (avatar && user.full_name) {
        avatar.textContent = user.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    }
    if (name) name.textContent = user.full_name || 'User';
    if (role) role.textContent = (user.role || 'user').replace('_', ' ');
}

// Chatbot
function openChatbot() {
    const modal = new bootstrap.Modal(document.getElementById('chatbotModal'));
    modal.show();
}

async function sendChat() {
    const input = document.getElementById('chatInput');
    const query = input.value.trim();
    if (!query) return;

    const messages = document.getElementById('chatMessages');

    // User message
    messages.innerHTML += `
        <div class="mb-3 text-end">
            <div class="d-inline-block p-3 rounded-3" style="background:#EEF2FF;max-width:80%">
                <small>${query}</small>
            </div>
        </div>`;

    input.value = '';
    messages.scrollTop = messages.scrollHeight;

    try {
        const data = await fetchAPI('/api/chatbot/query', {
            method: 'POST',
            body: JSON.stringify({ query }),
        });

        messages.innerHTML += `
            <div class="mb-3">
                <div class="d-flex gap-2">
                    <div style="width:32px;height:32px;background:var(--gradient-2);border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0">
                        <i class="bi bi-robot text-white" style="font-size:14px"></i>
                    </div>
                    <div class="p-3 rounded-3" style="background:#F1F5F9;max-width:80%">
                        <small style="white-space:pre-line">${data.response}</small>
                    </div>
                </div>
            </div>`;
    } catch (e) {
        messages.innerHTML += `
            <div class="mb-3">
                <div class="d-flex gap-2">
                    <div style="width:32px;height:32px;background:linear-gradient(135deg,#EF4444,#DC2626);border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0">
                        <i class="bi bi-exclamation text-white"></i>
                    </div>
                    <div class="p-3 rounded-3" style="background:#FEF2F2;max-width:80%">
                        <small>Sorry, something went wrong. Please try again.</small>
                    </div>
                </div>
            </div>`;
    }

    messages.scrollTop = messages.scrollHeight;
}

// Chat on Enter
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendChat();
        });
    }
    loadUserInfo();
});

// Export data
async function exportData(format) {
    const token = localStorage.getItem('access_token');
    try {
        const res = await fetch(`/api/export/invoices/${format}`, {
            headers: { 'Authorization': `Bearer ${token}` },
        });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `invoices.${format}`;
        a.click();
        URL.revokeObjectURL(url);
        showToast(`Exported as ${format.toUpperCase()}`, 'success');
    } catch (e) {
        showToast('Export failed', 'error');
    }
}
