/**
 * Test List Page
 */
import { listTests, deleteTest, stopTest } from '../api.js';
import { navigate, showToast, formatTimestamp, statusLabel, statusClass, isTestRunning, iconSvg, escapeHtml, debounce } from '../utils.js';

let state = {
  tests: [],
  total: 0,
  page: 1,
  pageSize: 15,
  statusFilter: '',
  searchTerm: '',
  refreshTimer: null,
  deleteTargetId: null,
};

let initialRender = true;

export async function render() {
  await fetchTests();
  initialRender = true;
  return renderHtml();
}

export function init() {
  if (initialRender) {
    bindEvents();
    initialRender = false;
  }
}

export function cleanup() {
  if (state.refreshTimer) {
    clearInterval(state.refreshTimer);
    state.refreshTimer = null;
  }
}

function renderHtml() {
  const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
  const hasRunning = state.tests.some(t => isTestRunning(t.status));

  return `
    <div>
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800 flex items-center gap-2">
            ${iconSvg('bar-chart', 22)} 测试任务列表
          </h2>
          <p class="text-sm text-gray-500 mt-1">共 ${state.total} 个测试任务</p>
        </div>
        <div class="flex items-center gap-2">
          ${hasRunning ? `
            <span class="flex items-center gap-1 text-xs text-blue-600">
              <span class="status-dot running"></span> 自动刷新中
            </span>
          ` : ''}
          <button class="btn btn-secondary btn-sm" id="refresh-btn">
            ${iconSvg('refresh', 14)} 刷新
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="card p-3 mb-4">
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2">
            <label class="text-xs text-gray-500">状态:</label>
            <select class="form-select text-sm w-auto py-1.5" id="filter-status">
              <option value="" ${state.statusFilter === '' ? 'selected' : ''}>全部</option>
              <option value="pending" ${state.statusFilter === 'pending' ? 'selected' : ''}>等待中</option>
              <option value="running" ${state.statusFilter === 'running' ? 'selected' : ''}>运行中</option>
              <option value="completed" ${state.statusFilter === 'completed' ? 'selected' : ''}>已完成</option>
              <option value="failed" ${state.statusFilter === 'failed' ? 'selected' : ''}>失败</option>
              <option value="cancelled" ${state.statusFilter === 'cancelled' ? 'selected' : ''}>已取消</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <label class="text-xs text-gray-500">搜索:</label>
            <input type="text" class="form-input text-sm w-48 py-1.5" id="filter-search"
              placeholder="名称或 ID..." value="${escapeHtml(state.searchTerm)}">
          </div>
          <button class="btn btn-primary btn-sm ml-auto" onclick="window.navigateTo('/')">
            ${iconSvg('plus', 14)} 新建测试
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="card overflow-hidden">
        ${state.tests.length === 0 ? renderEmpty() : renderTable()}
      </div>

      <!-- Pagination -->
      ${totalPages > 1 ? renderPagination(state.page, totalPages) : ''}

      <!-- Delete confirmation modal -->
      <div id="delete-modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div class="bg-white rounded-xl p-6 max-w-sm w-full mx-4 shadow-xl animate-fade-in">
          <h3 class="text-lg font-bold text-gray-800 mb-2">确认删除</h3>
          <p class="text-sm text-gray-600 mb-4" id="delete-modal-text">确定要删除该测试吗？此操作不可撤销。</p>
          <div class="flex justify-end gap-2">
            <button class="btn btn-secondary" id="delete-cancel-btn">取消</button>
            <button class="btn btn-danger" id="delete-confirm-btn">删除</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderEmpty() {
  return `
    <div class="text-center py-16">
      <div class="text-4xl mb-3">📋</div>
      <p class="text-gray-400 text-sm">暂无测试任务</p>
      <button class="btn btn-primary mt-4" onclick="window.navigateTo('/')">
        ${iconSvg('plus', 14)} 新建测试
      </button>
    </div>
  `;
}

function renderTable() {
  return `
    <div class="overflow-x-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th class="w-16">ID</th>
            <th>名称</th>
            <th>类型</th>
            <th>状态</th>
            <th>进度</th>
            <th>创建时间</th>
            <th class="w-24">操作</th>
          </tr>
        </thead>
        <tbody>
          ${state.tests.map(t => {
            const subtaskCount = t.subtask_count || t.total_subtasks || 0;
            const completedCount = t.completed_count || t.completed_subtasks || 0;
            return `
              <tr onclick="window.navigateTo('/tests/${t.id}')">
                <td class="text-gray-400 text-xs font-mono">#${t.id}</td>
                <td class="font-medium text-gray-800 max-w-[200px] truncate" title="${escapeHtml(t.name || '')}">
                  ${escapeHtml(t.name || `测试-${t.id}`)}
                </td>
                <td class="text-sm text-gray-600">${escapeHtml(t.test_type || t.type || '-')}</td>
                <td>
                  <span class="status-badge ${statusClass(t.status)}">
                    <span class="status-dot ${t.status}"></span>
                    ${statusLabel(t.status)}
                  </span>
                </td>
                <td class="text-sm text-gray-600 font-mono">
                  ${subtaskCount > 0 ? `${completedCount}/${subtaskCount}` : '-'}
                </td>
                <td class="text-sm text-gray-500 whitespace-nowrap">
                  ${formatTimestamp(t.created_at)}
                </td>
                <td>
                  <div class="flex items-center gap-1" onclick="event.stopPropagation()">
                    ${isTestRunning(t.status) ? `
                      <button class="btn btn-secondary btn-sm" title="停止" id="stop-btn-${t.id}">
                        ${iconSvg('stop', 14)}
                      </button>
                    ` : ''}
                    <button class="btn btn-secondary btn-sm text-red-500 hover:text-red-600" title="删除" id="delete-btn-${t.id}">
                      ${iconSvg('trash', 14)}
                    </button>
                  </div>
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    </div>
  `;
}

function renderPagination(page, totalPages) {
  const pages = [];
  const maxVisible = 5;
  let start = Math.max(1, page - Math.floor(maxVisible / 2));
  let end = Math.min(totalPages, start + maxVisible - 1);
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1);
  }
  for (let i = start; i <= end; i++) pages.push(i);

  return `
    <div class="flex items-center justify-center gap-1 mt-4">
      <button class="pagination-btn" id="pagination-prev" ${page <= 1 ? 'disabled' : ''}>
        ${iconSvg('chevron-left', 16)}
      </button>
      ${start > 1 ? `<button class="pagination-btn" id="pagination-page-1">1</button>` : ''}
      ${start > 2 ? '<span class="px-2 text-gray-400">...</span>' : ''}
      ${pages.map(p => `
        <button class="pagination-btn ${p === page ? 'active' : ''}" id="pagination-page-${p}">
          ${p}
        </button>
      `).join('')}
      ${end < totalPages - 1 ? '<span class="px-2 text-gray-400">...</span>' : ''}
      ${end < totalPages ? `<button class="pagination-btn" id="pagination-page-${totalPages}">${totalPages}</button>` : ''}
      <button class="pagination-btn" id="pagination-next" ${page >= totalPages ? 'disabled' : ''}>
        ${iconSvg('chevron-right', 16)}
      </button>
    </div>
  `;
}

// ============ Data fetching ============
async function fetchTests() {
  try {
    const params = { page: state.page, page_size: state.pageSize };
    if (state.statusFilter) params.status = state.statusFilter;
    if (state.searchTerm) params.search = state.searchTerm;

    const result = await listTests(params);
    state.tests = result.items || result.tests || result.data || [];
    state.total = result.total || result.count || state.tests.length;

    const hasRunning = state.tests.some(t => isTestRunning(t.status));
    if (hasRunning && !state.refreshTimer) {
      state.refreshTimer = setInterval(() => fetchTestsAndRerender(), 5000);
    } else if (!hasRunning && state.refreshTimer) {
      clearInterval(state.refreshTimer);
      state.refreshTimer = null;
    }
    return result;
  } catch (err) {
    showToast(`加载测试列表失败: ${err.message}`, 'error');
    state.tests = [];
    state.total = 0;
  }
}

async function fetchTestsAndRerender() {
  await fetchTests();
  const app = document.getElementById('app-content');
  if (app) app.innerHTML = renderHtml();
  bindEvents();
}

// ============ Event bindings ============
function bindEvents() {
  // Status filter
  const statusFilter = document.getElementById('filter-status');
  if (statusFilter) {
    statusFilter.addEventListener('change', () => {
      state.statusFilter = statusFilter.value;
      state.page = 1;
      fetchTestsAndRerender();
    });
  }

  // Search
  const searchInput = document.getElementById('filter-search');
  if (searchInput) {
    const debouncedSearch = debounce(() => {
      state.searchTerm = searchInput.value;
      state.page = 1;
      fetchTestsAndRerender();
    }, 300);
    searchInput.addEventListener('input', debouncedSearch);
  }

  // Refresh button
  const refreshBtn = document.getElementById('refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      state.page = 1;
      fetchTestsAndRerender();
    });
  }

  // Pagination
  bindPagination(state.page, Math.max(1, Math.ceil(state.total / state.pageSize)));

  // Stop buttons
  state.tests.forEach(t => {
    if (isTestRunning(t.status)) {
      const btn = document.getElementById(`stop-btn-${t.id}`);
      if (btn) btn.addEventListener('click', () => handleStopTest(t.id));
    }
  });

  // Delete buttons
  state.tests.forEach(t => {
    const btn = document.getElementById(`delete-btn-${t.id}`);
    if (btn) btn.addEventListener('click', () => confirmDeleteTest(t.id, t.name));
  });

  // Delete modal
  const cancelBtn = document.getElementById('delete-cancel-btn');
  if (cancelBtn) cancelBtn.addEventListener('click', closeDeleteModal);

  const confirmBtn = document.getElementById('delete-confirm-btn');
  if (confirmBtn) confirmBtn.addEventListener('click', handleDeleteConfirm);
}

function bindPagination(page, totalPages) {
  const prevBtn = document.getElementById('pagination-prev');
  if (prevBtn) prevBtn.addEventListener('click', () => goToPage(page - 1));

  const nextBtn = document.getElementById('pagination-next');
  if (nextBtn) nextBtn.addEventListener('click', () => goToPage(page + 1));

  for (let p = 1; p <= totalPages; p++) {
    const btn = document.getElementById(`pagination-page-${p}`);
    if (btn) btn.addEventListener('click', () => goToPage(p));
  }
}

function goToPage(page) {
  state.page = page;
  fetchTestsAndRerender();
}

async function handleStopTest(id) {
  try {
    await stopTest(id);
    showToast('测试已停止', 'success');
    fetchTestsAndRerender();
  } catch (err) {
    showToast(`停止失败: ${err.message}`, 'error');
  }
}

function confirmDeleteTest(id, name) {
  state.deleteTargetId = id;
  const modal = document.getElementById('delete-modal');
  const text = document.getElementById('delete-modal-text');
  if (modal) modal.classList.remove('hidden');
  if (text) text.textContent = `确定要删除测试 "${name || '#' + id}" 吗？此操作不可撤销。`;
}

function closeDeleteModal() {
  state.deleteTargetId = null;
  const modal = document.getElementById('delete-modal');
  if (modal) modal.classList.add('hidden');
}

async function handleDeleteConfirm() {
  if (!state.deleteTargetId) return;
  try {
    await deleteTest(state.deleteTargetId);
    showToast('测试已删除', 'success');
    closeDeleteModal();
    fetchTestsAndRerender();
  } catch (err) {
    showToast(`删除失败: ${err.message}`, 'error');
  }
}

// Global navigation
window.navigateTo = (hash) => navigate(hash);
