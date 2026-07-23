/**
 * Metrics Card component - Display structured metrics in a comparison table
 */
import { formatNumber, formatDuration, iconSvg, escapeHtml } from '../utils.js';

/** Parse result field (backend returns JSON string) */
function parseResult(result) {
  if (!result) return {};
  if (typeof result === 'string') {
    try { return JSON.parse(result); } catch (e) { return {}; }
  }
  return result;
}

/**
 * Render metrics comparison table for subtasks
 */
export function renderMetricsCard(subtasks, testData) {
  if (!subtasks || subtasks.length === 0) {
    return `
      <div class="card p-5">
        <h3 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
          ${iconSvg('bar-chart', 16)} 汇总指标
        </h3>
        <p class="text-sm text-gray-400 text-center py-4">暂无指标数据</p>
      </div>
    `;
  }

  // Collect all completed subtasks with parsed results
  const subtasksParsed = subtasks.map(s => ({ ...s, _parsed: parseResult(s.result) }));
  const completed = subtasksParsed.filter(s => s.status === 'completed' && Object.keys(s._parsed).length > 0);
  if (completed.length === 0) {
    return renderSubtaskSummary(subtasksParsed);
  }

  // Extract sweep param key and collect all metric keys
  const sweepKey = testData?.sweep_key || 'max_concurrency';
  const allMetrics = collectMetrics(completed);

  if (allMetrics.length === 0) {
    return renderSubtaskSummary(subtasksParsed);
  }

  // Find best values for highlighting (lower is better for latency, higher for throughput)
  const lowerIsBetter = ['ttft', 'avg_latency', 'total_latency', 'p50_latency', 'p95_latency', 'p99_latency', 'avg_ttft', 'avg_tpot', 'qps'];
  const bestValues = {};
  for (const metric of allMetrics) {
    const isLowerBetter = lowerIsBetter.some(k => metric.key.toLowerCase().includes(k));
    const values = completed.map(s => s._parsed[metric.key]).filter(v => v != null);
    if (values.length > 0) {
      bestValues[metric.key] = isLowerBetter ? Math.min(...values) : Math.max(...values);
    }
  }

  return `
    <div class="card p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
        ${iconSvg('bar-chart', 16)} 汇总指标对比
        <span class="text-xs text-gray-400 font-normal">
          (${escapeHtml(sweepKey)})
        </span>
      </h3>

      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>${escapeHtml(sweepKey)}</th>
              <th>状态</th>
              ${allMetrics.map(m => `<th>${escapeHtml(m.label)}</th>`).join('')}
            </tr>
          </thead>
          <tbody>
            ${subtasksParsed.map((s, i) => {
              const result = s._parsed || {};
              const sweepVal = s.params ? (() => { try { return JSON.parse(s.params)[sweepKey]; } catch(e) { return '-'; } })() : '-';
              return `
                <tr>
                  <td class="text-gray-400 text-xs">#${s.seq || i + 1}</td>
                  <td class="font-mono text-sm">${escapeHtml(String(sweepVal))}</td>
                  <td>${renderStatusBadge(s.status)}</td>
                  ${allMetrics.map(m => {
                    const val = result[m.key];
                    const isBest = s.status === 'completed' && val != null && val === bestValues[m.key];
                    return `<td class="${isBest ? 'metric-best' : ''} font-mono text-sm">${formatMetricValue(val, m.key)}</td>`;
                  }).join('')}
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
      ${renderBestLegend()}
    </div>
  `;
}

function renderSubtaskSummary(subtasks) {
  return `
    <div class="card p-5">
      <h3 class="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
        ${iconSvg('bar-chart', 16)} 子任务结果
      </h3>
      <div class="space-y-2">
        ${subtasks.map((s, i) => {
          let sweepVal = '-';
          if (s.params) {
            try { sweepVal = JSON.stringify(JSON.parse(s.params)); } catch(e) { sweepVal = s.params; }
          }
          return `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div class="flex items-center gap-3">
                <span class="text-xs text-gray-400 font-mono">#${s.seq || i + 1}</span>
                <span class="text-xs text-gray-600 font-mono">${escapeHtml(sweepVal.substring(0, 100))}</span>
              </div>
              <div class="flex items-center gap-2">
                ${renderStatusBadge(s.status)}
                ${s._parsed ? renderBriefResult(s._parsed) : ''}
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}

function renderBriefResult(result) {
  const items = [];
  if (result.avg_ttft != null) items.push(`TTFT: ${formatNumber(result.avg_ttft)}ms`);
  if (result.throughput != null) items.push(`吞吐: ${formatNumber(result.throughput)} tok/s`);
  if (result.total_latency != null) items.push(`延迟: ${formatNumber(result.total_latency)}s`);
  if (items.length === 0) return '';
  return `<span class="text-xs text-gray-500 font-mono">${items.join(' | ')}</span>`;
}

function renderStatusBadge(status) {
  const map = {
    pending: { cls: 'status-pending', text: '⏳ 等待', dot: 'pending' },
    running: { cls: 'status-running', text: '🔄 运行中', dot: 'running' },
    completed: { cls: 'status-completed', text: '✅ 完成', dot: 'completed' },
    failed: { cls: 'status-failed', text: '❌ 失败', dot: 'failed' },
    cancelled: { cls: 'status-cancelled', text: '⏹ 已取消', dot: 'cancelled' },
  };
  const info = map[status] || map.pending;
  return `<span class="status-badge ${info.cls}"><span class="status-dot ${info.dot}"></span> ${info.text}</span>`;
}

function renderBestLegend() {
  return `<p class="text-xs text-gray-400 mt-3"><span class="metric-best">绿色高亮</span> = 该指标最优值</p>`;
}

/**
 * Collect all metric keys from completed subtasks
 */
function collectMetrics(subtasks) {
  const seen = new Set();
  const metrics = [];

  const priority = [
    'qps', 'avg_latency_s', 'p50_latency_s', 'p90_latency_s', 'p99_latency_s',
    'avg_ttft', 'input_throughput', 'output_throughput', 'total_time_s',
    'total_requests', 'avg_input_tokens',
  ];

  // Find first completed subtask with parsed result
  let anyResult = null;
  for (const s of subtasks) {
    if (s._parsed && Object.keys(s._parsed).length > 0) {
      anyResult = s._parsed;
      break;
    }
  }
  if (!anyResult) return metrics;

  // Try priority order first
  for (const key of priority) {
    if (anyResult[key] != null && !seen.has(key)) {
      seen.add(key);
      metrics.push({ key, label: formatMetricLabel(key) });
    }
  }

  // Then add any remaining keys
  for (const key of Object.keys(anyResult)) {
    if (!seen.has(key) && !key.startsWith('_')) {
      seen.add(key);
      metrics.push({ key, label: formatMetricLabel(key) });
    }
  }

  return metrics;
}

function formatMetricLabel(key) {
  const labels = {
    // Chat metrics
    'avg_ttft': '平均TTFT(ms)',
    'input_throughput': '输入吞吐(tok/s)',
    'output_throughput': '输出吞吐(tok/s)',
    'total_time_s': '总耗时(s)',
    'avg_tpot': '平均TPOT(ms)',
    'avg_total_time': '平均总延迟(s)',
    // Embedding metrics
    'qps': 'QPS(请求/s)',
    'avg_latency_s': '平均延迟(s)',
    'p50_latency_s': 'P50延迟(s)',
    'p90_latency_s': 'P90延迟(s)',
    'p99_latency_s': 'P99延迟(s)',
    'min_latency_s': '最小延迟(s)',
    'max_latency_s': '最大延迟(s)',
    // Common
    'total_requests': '总请求数',
    'avg_input_tokens': '平均输入Tokens',
    'model_name': '模型名',
    'max_concurrency': '最大并发',
  };
  return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function formatMetricValue(val, key) {
  if (val == null) return '-';
  if (typeof val === 'object') return JSON.stringify(val);
  if (typeof val === 'number') {
    const intKeys = ['total_requests', 'success_count', 'fail_count'];
    if (intKeys.includes(key)) return String(Math.round(val));
    return formatNumber(val, 2);
  }
  return String(val);
}
