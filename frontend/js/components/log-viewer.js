/**
 * Log Viewer component - Terminal-like real-time log display
 */
import { createLogWebSocket, getTestLogs } from '../api.js';
import { escapeHtml, iconSvg } from '../utils.js';

/**
 * Create and manage a log viewer instance
 */
export class LogViewer {
  constructor(containerId, testId) {
    this.container = document.getElementById(containerId);
    this.testId = testId;
    this.logs = [];
    this.autoScroll = true;
    this.ws = null;
    this.pollTimer = null;
    this.lastTimestamp = null;
    this.isWebSocketConnected = false;
    this.destroyed = false;
  }

  render() {
    if (!this.container) return;
    const logContent = this.logs.map(log => this.formatLogLine(log)).join('');

    this.container.innerHTML = `
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
          ${iconSvg('file', 16)} 实时日志
          <span class="inline-flex items-center gap-1" id="log-connection-status">
            <span class="status-dot" id="log-dot" style="background:#9ca3af"></span>
            <span class="text-xs text-gray-400" id="log-status-text">连接中...</span>
          </span>
        </h3>
        <div class="flex items-center gap-2">
          <button class="btn btn-secondary btn-sm" id="log-clear-btn" title="清空日志">清空</button>
          ${!this.autoScroll ? `
            <button class="btn btn-secondary btn-sm" id="log-scroll-btn" title="滚到底部">⬇ 最新</button>
          ` : ''}
        </div>
      </div>
      <div class="log-terminal" id="log-content">${logContent || '<span class="text-gray-500">等待日志输出...</span>'}</div>
    `;

    this.bindEvents();
  }

  formatLogLine(log) {
    if (!log) return '';
    if (typeof log === 'string') return escapeHtml(log) + '\n';

    const timestamp = log.timestamp ? `<span class="text-gray-500 text-xs">[${new Date(log.timestamp).toLocaleTimeString()}]</span> ` : '';
    const subtaskPrefix = log.subtask_id ? `<span class="text-yellow-400">[子任务#${log.subtask_id}]</span> ` : '';

    let message = log.message || log.content || log.text || JSON.stringify(log);
    message = escapeHtml(message);

    // Highlight log levels
    if (log.level === 'ERROR' || log.level === 'error') {
      message = `<span class="text-red-400">${message}</span>`;
    } else if (log.level === 'WARNING' || log.level === 'warning') {
      message = `<span class="text-yellow-300">${message}</span>`;
    } else if (log.separator) {
      return `<div class="log-separator">${'='.repeat(60)}</div>`;
    }

    return `${timestamp}${subtaskPrefix}${message}\n`;
  }

  bindEvents() {
    const logContent = document.getElementById('log-content');
    if (logContent) {
      logContent.addEventListener('scroll', () => {
        const threshold = 50;
        this.autoScroll = logContent.scrollHeight - logContent.scrollTop - logContent.clientHeight < threshold;
        this.render();
      });
    }

    const clearBtn = document.getElementById('log-clear-btn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        this.logs = [];
        this.render();
      });
    }

    const scrollBtn = document.getElementById('log-scroll-btn');
    if (scrollBtn) {
      scrollBtn.addEventListener('click', () => {
        this.autoScroll = true;
        this.scrollToBottom();
        this.render();
      });
    }
  }

  scrollToBottom() {
    const logContent = document.getElementById('log-content');
    if (logContent) {
      logContent.scrollTop = logContent.scrollHeight;
    }
  }

  appendLog(log) {
    this.logs.push(log);
    // Limit log buffer
    if (this.logs.length > 5000) {
      this.logs = this.logs.slice(-3000);
    }
    this.render();
    if (this.autoScroll) {
      requestAnimationFrame(() => this.scrollToBottom());
    }
  }

  appendLogs(logs) {
    for (const log of logs) {
      this.logs.push(log);
    }
    if (this.logs.length > 5000) {
      this.logs = this.logs.slice(-3000);
    }
    this.render();
    if (this.autoScroll) {
      requestAnimationFrame(() => this.scrollToBottom());
    }
  }

  setConnectionStatus(connected) {
    this.isWebSocketConnected = connected;
    const dot = document.getElementById('log-dot');
    const text = document.getElementById('log-status-text');
    if (dot) dot.style.background = connected ? '#22c55e' : '#9ca3af';
    if (text) text.textContent = connected ? 'WS 已连接' : '轮询中...';
  }

  /**
   * Connect via WebSocket for real-time logs
   */
  connectWebSocket() {
    if (this.destroyed) return;
    try {
      this.ws = createLogWebSocket(this.testId);

      this.ws.onopen = () => {
        if (this.destroyed) return;
        this.setConnectionStatus(true);
      };

      this.ws.onmessage = (event) => {
        if (this.destroyed) return;
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'log' || data.message != null) {
            this.appendLog(data);
          } else if (Array.isArray(data)) {
            this.appendLogs(data);
          } else {
            this.appendLog(data);
          }
        } catch (_) {
          this.appendLog({ message: event.data });
        }
      };

      this.ws.onclose = () => {
        if (this.destroyed) return;
        this.setConnectionStatus(false);
        // Fallback to polling
        this.startPolling();
      };

      this.ws.onerror = () => {
        if (this.destroyed) return;
        this.setConnectionStatus(false);
        this.startPolling();
      };
    } catch (_) {
      this.startPolling();
    }
  }

  /**
   * Fallback: Poll for new logs
   */
  startPolling() {
    if (this.pollTimer || this.destroyed) return;
    this.pollTimer = setInterval(() => {
      if (this.destroyed || this.isWebSocketConnected) {
        this.stopPolling();
        return;
      }
      this.fetchLogs();
    }, 2000);
    // Fetch immediately
    this.fetchLogs();
  }

  async fetchLogs() {
    try {
      const params = { limit: 100 };
      if (this.lastTimestamp) {
        params.after_timestamp = this.lastTimestamp;
      }
      const result = await getTestLogs(this.testId, params);
      const logs = result.logs || result || [];
      if (Array.isArray(logs) && logs.length > 0) {
        this.appendLogs(logs);
        // Update last timestamp
        const last = logs[logs.length - 1];
        this.lastTimestamp = last.timestamp || last.created_at || Date.now();
      }
    } catch (_) { /* silent fail on polling */ }
  }

  stopPolling() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  destroy() {
    this.destroyed = true;
    this.stopPolling();
    if (this.ws) {
      try { this.ws.close(); } catch (_) { /* ignore */ }
      this.ws = null;
    }
  }
}
