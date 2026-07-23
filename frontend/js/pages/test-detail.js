/**
 * Test Detail Page - Test detail with live logs
 */
import { getTest, stopTest } from '../api.js';
import { LogViewer } from '../components/log-viewer.js';
import { renderMetricsCard } from '../components/metrics-card.js';
import {
  showToast, navigate, formatTimestamp, formatDateTime,
  statusLabel, statusClass, isTestRunning, iconSvg, escapeHtml
} from '../utils.js';

let state = {
  testId: null,
  testData: null,
  logViewer: null,
  refreshTimer: null,
};

export async function render(params) {
  const id = params.id;
  if (!id) {
    return `<div class="text-center py-16 text-gray-400">无效的测试 ID</div>`;
  }
  state.testId = id;

  try {
    state.testData = await getTest(id);
  } catch (err) {
    return `
      <div class="text-center py-16">
        <div class="text-4xl mb-4">⚠️</div>
        <h2 class="text-xl font-bold text-gray-700 mb-2">加载测试详情失败</h2>
        <p class="text-gray-500">${escapeHtml(err.message)}</p>
        <button class="btn btn-primary mt-4" onclick="window.navigateTo('/tests')">
          ${iconSvg('arrow-left', 14)} 返回列表
        </button>
      </div>
    `;
  }

  return renderHtml();
}

export function cleanup() {
  cleanupResources();
}

function cleanupResources() {
  if (state.refreshTimer) {
    clearInterval(state.refreshTimer);
    state.refreshTimer = null;
  }
  if (state.logViewer) {
    state.logViewer.destroy();
    state.logViewer = null;
  }
}

function renderHtml() {
  const data = state.testData;
  if (!data) return '<div class="text-center py-16 text-gray-400">无数据</div>';

  const subtasks = data.subtasks || data.children || [];
  const isRunning = isTestRunning(data.status);
  const subtaskCount = subtasks.length;
  const completedCount = subtasks.filter(s => s.status === 'completed').length;

  return `
    <div>
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <button class="btn btn-secondary btn-sm" onclick="window.navigateTo('/tests')">
            ${iconSvg('arrow-left', 14)} 返回列表
          </button>
          <div>
            <h2 class="text-xl font-bold text-gray-800 flex items-center gap-2">
              测试详情 <span class="text-gray-400 text-base font-mono">#${data.id}</span>
            </h2>
            <p class="text-sm text-gray-500">${escapeHtml(data.name || `测试-${data.id}`)}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          ${isRunning ? `
            <button class="btn btn-danger btn-sm" id="stop-test-btn">
              ${iconSvg('stop', 14)} 停止测试
            </button>
          ` : ''}
          <button class="btn btn-secondary btn-sm" id="refresh-detail-btn">
            ${iconSvg('refresh', 14)} 刷新
          </button>
        </div>
      </div>

      <!-- Status Bar -->
      <div class="card p-4 mb-4">
        <div class="flex flex-wrap items-center gap-6">
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500">状态:</span>
            <span class="status-badge ${statusClass(data.status)}">
              <span class="status-dot ${data.status}"></span>
              ${statusLabel(data.status)}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500">类型:</span>
            <span class="text-sm font-medium text-gray-700">${escapeHtml(data.test_type || data.type || '-')}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500">进度:</span>
            <span class="text-sm font-mono text-gray-700">${completedCount}/${subtaskCount}</span>
            ${subtaskCount > 0 ? `
              <div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div class="h-full bg-blue-600 rounded-full transition-all duration-300"
                  style="width:${Math.round((completedCount / subtaskCount) * 100)}%">
                </div>
              </div>
            ` : ''}
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500">创建时间:</span>
            <span class="text-sm text-gray-700">${formatDateTime(data.created_at)}</span>
          </div>
          ${data.started_at ? `
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-500">开始时间:</span>
              <span class="text-sm text-gray-700">${formatDateTime(data.started_at)}</span>
            </div>
          ` : ''}
        </div>
      </div>

      <!-- Log Viewer -->
      <div class="card p-4 mb-4" id="log-viewer-container">
        <!-- Rendered by LogViewer -->
      </div>

      <!-- Subtask Results -->
      <div class="mb-4">
        ${renderMetricsCard(subtasks, data)}
      </div>

      <!-- Error message -->
      ${data.error_message ? `
        <div class="card p-4 mb-4 border-l-4 border-red-500 bg-red-50">
          <h4 class="text-sm font-semibold text-red-700 mb-1">错误信息</h4>
          <pre class="text-sm text-red-600 whitespace-pre-wrap font-mono">${escapeHtml(data.error_message)}</pre>
        </div>
      ` : ''}
    </div>
  `;
}

/**
 * Initialize the log viewer and event listeners (called after render)
 */
export function init() {
  // Log viewer
  if (state.testId) {
    state.logViewer = new LogViewer('log-viewer-container', state.testId);
    state.logViewer.render();
    state.logViewer.connectWebSocket();
  }

  bindEvents();

  // Auto-refresh for running tests
  if (state.testData && isTestRunning(state.testData.status)) {
    state.refreshTimer = setInterval(refreshTestData, 3000);
  }
}

function bindEvents() {
  const stopBtn = document.getElementById('stop-test-btn');
  if (stopBtn) {
    stopBtn.addEventListener('click', handleStopTest);
  }

  const refreshBtn = document.getElementById('refresh-detail-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => refreshTestData());
  }
}

async function handleStopTest() {
  if (!state.testId) return;
  const btn = document.getElementById('stop-test-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="loader"></span> 停止中...';
  }
  try {
    await stopTest(state.testId);
    showToast('测试已停止', 'success');
    refreshTestData();
  } catch (err) {
    showToast(`停止失败: ${err.message}`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `${iconSvg('stop', 14)} 停止测试`;
    }
  }
}

async function refreshTestData() {
  if (!state.testId) return;
  try {
    const data = await getTest(state.testId);
    const wasRunning = state.testData && isTestRunning(state.testData.status);
    state.testData = data;
    const isRunning = isTestRunning(data.status);

    // Re-render
    const app = document.getElementById('app-content');
    if (app) {
      cleanupResources();
      app.innerHTML = renderHtml();
      init();
    }

    // Stop auto-refresh if test is no longer running
    if (!isRunning && state.refreshTimer) {
      clearInterval(state.refreshTimer);
      state.refreshTimer = null;
    }
    // Start auto-refresh if test just started running
    if (isRunning && !state.refreshTimer) {
      state.refreshTimer = setInterval(refreshTestData, 3000);
    }
  } catch (err) {
    showToast(`刷新失败: ${err.message}`, 'error');
  }
}

window.navigateTo = navigate;
