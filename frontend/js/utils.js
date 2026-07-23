/**
 * Utility functions
 */

export function formatTimestamp(ts) {
  if (!ts) return '-';
  const d = new Date(ts);
  const now = new Date();
  const diff = now - d;
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

export function formatDateTime(ts) {
  if (!ts) return '-';
  return new Date(ts).toLocaleString('zh-CN');
}

export function formatDuration(seconds) {
  if (seconds == null) return '-';
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
  if (seconds < 60) return `${seconds.toFixed(2)}s`;
  const m = Math.floor(seconds / 60);
  const s = (seconds % 60).toFixed(0);
  return `${m}m ${s}s`;
}

export function formatNumber(n, digits = 2) {
  if (n == null) return '-';
  if (typeof n !== 'number') return String(n);
  return n.toFixed(digits);
}

export function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export function statusLabel(status) {
  const map = { pending: '等待中', running: '运行中', completed: '已完成', failed: '失败', cancelled: '已取消' };
  return map[status] || status;
}

export function statusClass(status) {
  return `status-${status || 'pending'}`;
}

export function generateTestName(testType) {
  const now = new Date();
  const ts = `${now.getMonth() + 1}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
  return `${testType || 'test'}_${ts}`;
}

/**
 * Simple toast notification
 */
export function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  toast.innerHTML = `<span>${icons[type] || ''}</span><span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/**
 * Simple debounce
 */
export function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Check if a test is still running
 */
export function isTestRunning(status) {
  return status === 'pending' || status === 'running';
}

/**
 * Parse hash route: /tests/5 -> { page: 'test-detail', params: { id: '5' } }
 */
export function parseRoute() {
  const hash = window.location.hash.replace('#', '') || '/';
  const parts = hash.split('/').filter(Boolean);
  if (parts.length === 0) return { page: 'new-test', params: {} };
  if (parts[0] === 'tests') {
    if (parts.length >= 2) return { page: 'test-detail', params: { id: parts[1] } };
    return { page: 'test-list', params: {} };
  }
  if (parts[0] === 'new-test') return { page: 'new-test', params: {} };
  return { page: 'new-test', params: {} };
}

/**
 * Navigate to a hash route
 */
export function navigate(hash) {
  window.location.hash = hash;
}

/**
 * Create an HTML element with attributes and children
 */
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, val] of Object.entries(attrs)) {
    if (key === 'className') {
      el.className = val;
    } else if (key === 'innerHTML') {
      el.innerHTML = val;
    } else if (key.startsWith('on') && typeof val === 'function') {
      el.addEventListener(key.slice(2).toLowerCase(), val);
    } else if (key === 'style' && typeof val === 'object') {
      Object.assign(el.style, val);
    } else {
      el.setAttribute(key, val);
    }
  }
  for (const child of children) {
    if (child == null) continue;
    if (typeof child === 'string' || typeof child === 'number') {
      el.appendChild(document.createTextNode(String(child)));
    } else if (child instanceof Node) {
      el.appendChild(child);
    }
  }
  return el;
}

/**
 * SVG icon helper - inline SVG paths
 */
export const icons = {
  'play': '<path d="M5 3l14 9-14 9V3z" fill="currentColor"/>',
  'stop': '<rect x="4" y="4" width="16" height="16" rx="2" fill="currentColor"/>',
  'trash': '<path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6M10 11v6M14 11v6" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round"/>',
  'refresh': '<path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  'chevron-left': '<path d="M15 18l-6-6 6-6" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  'chevron-right': '<path d="M9 18l6-6-6-6" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  'plus': '<path d="M12 5v14M5 12h14" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round"/>',
  'x': '<path d="M18 6L6 18M6 6l12 12" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round"/>',
  'check': '<path d="M20 6L9 17l-5-5" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  'file': '<path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z" stroke="currentColor" fill="none" stroke-width="2"/><path d="M13 2v7h7" stroke="currentColor" fill="none" stroke-width="2"/>',
  'folder': '<path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" stroke="currentColor" fill="none" stroke-width="2"/>',
  'download': '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  'search': '<circle cx="11" cy="11" r="8" stroke="currentColor" fill="none" stroke-width="2"/><path d="M21 21l-4.35-4.35" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round"/>',
  'zap': '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="currentColor"/>',
  'clock': '<circle cx="12" cy="12" r="10" stroke="currentColor" fill="none" stroke-width="2"/><path d="M12 6v6l4 2" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round"/>',
  'settings': '<circle cx="12" cy="12" r="3" stroke="currentColor" fill="none" stroke-width="2"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" fill="none" stroke-width="2"/>',
  'bar-chart': '<path d="M18 20V10M12 20V4M6 20v-6" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  'database': '<ellipse cx="12" cy="5" rx="9" ry="3" stroke="currentColor" fill="none" stroke-width="2"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" stroke="currentColor" fill="none" stroke-width="2"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" stroke="currentColor" fill="none" stroke-width="2"/>',
  'link': '<path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round"/>',
  'arrow-left': '<path d="M19 12H5M12 19l-7-7 7-7" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
};

export function iconSvg(name, size = 16, className = '') {
  const path = icons[name] || '';
  return `<svg class="${className}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">${path}</svg>`;
}

export function createIcon(name, size = 16, className = '') {
  const div = document.createElement('span');
  div.className = className;
  div.innerHTML = iconSvg(name, size);
  return div.firstElementChild;
}
