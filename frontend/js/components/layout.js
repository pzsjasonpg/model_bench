/**
 * Layout component - Navbar and content container
 */
import { navigate, parseRoute, iconSvg } from '../utils.js';

export function renderLayout(contentHtml) {
  const route = parseRoute();
  const navItems = [
    { label: '新建测试', hash: '/', icon: 'zap', active: route.page === 'new-test' },
    { label: '任务列表', hash: '/tests', icon: 'bar-chart', active: route.page === 'test-list' || route.page === 'test-detail' },
    { label: '数据集', hash: '/datasets', icon: 'database', active: route.page === 'datasets' },
  ];

  return `
    <div class="navbar px-4 py-3">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-2xl">⚡</span>
          <h1 class="text-white text-lg font-bold tracking-wide">模型性能测试平台</h1>
        </div>
        <nav class="flex items-center gap-1">
          ${navItems.map(item => `
            <button
              class="nav-tab px-4 py-2 text-sm font-medium text-white/80 rounded-lg ${item.active ? 'active text-white' : ''}"
              onclick="window.navigateTo('${item.hash}')"
              data-hash="${item.hash}"
            >
              <span class="inline-flex items-center gap-1.5">
                ${iconSvg(item.icon, 16)}
                ${item.label}
              </span>
            </button>
          `).join('')}
        </nav>
      </div>
    </div>
    <main class="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
      ${contentHtml}
    </main>
  `;
}

// Expose navigateTo globally for onclick handlers
window.navigateTo = (hash) => navigate(hash);
