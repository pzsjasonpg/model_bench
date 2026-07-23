/**
 * Test Form component - Dynamic test configuration form
 */
import { createTest, getTestTypes } from '../api.js';
import { showToast, navigate, generateTestName, iconSvg, escapeHtml } from '../utils.js';

const CATEGORY_LABELS = { chat: 'Chat 测试', embedding: 'Embedding 测试' };

// ── Form State ───────────────────────────────────────────────────────
const formState = {
  testTypes: null,
  selectedCategory: null,
  selectedType: null,        // the full test type object from backend
  sweepValues: [],
};

function getSweepState() { return formState; }

// ── Render: Test Type Cards ──────────────────────────────────────────
function renderTestTypeCards() {
  const types = formState.testTypes;
  if (!types || types.length === 0) {
    return '<div class="text-center py-8 text-gray-400">加载测试类型失败，请检查后端是否运行。</div>';
  }

  // Group by category
  const groups = {};
  for (const t of types) {
    const cat = t.category || 'other';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(t);
  }
  const catNames = Object.keys(groups);
  const currentCat = formState.selectedCategory || catNames[0];

  return `
    <!-- Category tabs -->
    <div class="flex gap-2 mb-4 flex-wrap">
      ${catNames.map(cat => `
        <button
          class="px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${cat === currentCat ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'}"
          onclick="window.selectCat('${escapeHtml(cat)}')"
        >${escapeHtml(CATEGORY_LABELS[cat] || cat)}</button>
      `).join('')}
    </div>

    <!-- Test type cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
      ${(groups[currentCat] || []).map(t => {
        const sel = formState.selectedType && formState.selectedType.type === t.type;
        return `
          <div class="test-type-card card p-4 cursor-pointer ${sel ? 'selected border-2 border-blue-500 bg-blue-50' : ''}"
               onclick="window.selectTestType('${escapeHtml(t.type)}')">
            <h3 class="font-semibold text-gray-800 text-sm">${escapeHtml(t.label)}</h3>
            <p class="text-xs text-gray-500 mt-1">${escapeHtml(t.description || '')}</p>
          </div>`;
      }).join('')}
    </div>
  `;
}

// ── Render: Test Form ────────────────────────────────────────────────
function renderTestForm() {
  const t = formState.selectedType;
  if (!t) return '';

  const hasSweep = !!t.sweep_config;
  const sweepKey = hasSweep ? t.sweep_config.key : '';
  const sweepLabel = hasSweep ? t.sweep_config.label : '';
  const hasModel = t.fixed_params && t.fixed_params.some(p => p.key === 'model_type' || p.key === 'base_url');
  const fixedParams = (t.fixed_params || []).filter(p => !hasModel || !['model_type', 'api_key', 'model', 'base_url', 'enable_thinking'].includes(p.key));

  return `
    <div class="card p-5 animate-fade-in mt-4">
      <h3 class="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
        ${iconSvg('settings', 18)} 测试配置
      </h3>
      <!-- Test name -->
      <div class="form-group">
        <label class="form-label">测试名称 <span class="text-gray-400 font-normal">(可选)</span></label>
        <input type="text" class="form-input" id="form-test-name"
          placeholder="${escapeHtml(generateTestName(t.label))}" value="">
      </div>

      ${hasModel ? renderModelConfig() : ''}
      ${renderFixedParams(fixedParams)}
      ${hasSweep ? renderSweepParams(sweepLabel, sweepKey) : ''}

      <!-- Submit -->
      <div class="mt-6 pt-4 border-t border-gray-100">
        <button class="btn btn-primary btn-lg w-full" id="form-submit-btn"
          onclick="window.submitTest()">
          ${iconSvg('play', 18)} 提交测试
        </button>
        <p class="text-xs text-gray-400 text-center mt-2" id="form-subtask-hint">
          ${hasSweep ? `将生成 <strong>${formState.sweepValues.length}</strong> 个子任务` : '将生成 1 个子任务'}
        </p>
      </div>
    </div>
  `;
}

function renderModelConfig() {
  const t = formState.selectedType;
  const defaults = t.default_fixed || {};
  return `
    <div class="mb-4 p-4 bg-blue-50/50 rounded-lg border border-blue-100">
      <h4 class="text-sm font-semibold text-blue-900 mb-3 flex items-center gap-1.5">
        ${iconSvg('link', 14)} 模型连接配置
      </h4>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div class="form-group">
          <label class="form-label">模型类型</label>
          <select class="form-select" id="form-model_type">
            <option value="openai" ${defaults.model_type === 'openai' ? 'selected' : ''}>OpenAI 兼容</option>
            <option value="mock" ${defaults.model_type === 'mock' ? 'selected' : ''}>Mock (模拟)</option>
            <option value="local" ${defaults.model_type === 'local' ? 'selected' : ''}>本地模型</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">模型名称</label>
          <input type="text" class="form-input" id="form-model" placeholder="如: Qwen3-8B" value="${escapeHtml(defaults.model || '')}">
        </div>
        <div class="form-group">
          <label class="form-label">API Key</label>
          <input type="text" class="form-input" id="form-api_key" placeholder="输入 API Key" value="${escapeHtml(defaults.api_key || '')}">
        </div>
        <div class="form-group">
          <label class="form-label">Base URL</label>
          <input type="text" class="form-input" id="form-base_url" placeholder="http://localhost:8000/v1" value="${escapeHtml(defaults.base_url || '')}">
        </div>
      </div>
      <div class="form-group mt-2">
        <label class="inline-flex items-center gap-2 cursor-pointer">
          <input type="checkbox" class="form-checkbox" id="form-enable_thinking" ${defaults.enable_thinking ? 'checked' : ''}>
          <span class="text-sm text-gray-700">启用思考模式</span>
        </label>
      </div>
    </div>
  `;
}

function renderFixedParams(params) {
  if (!params || params.length === 0) {
    return '<p class="text-sm text-gray-400 py-2">无额外固定参数。</p>';
  }
  return `
    <div class="mb-4">
      <h4 class="text-sm font-semibold text-gray-700 mb-3">📌 固定参数</h4>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        ${params.map(p => renderParamInput(p)).join('')}
      </div>
    </div>
  `;
}

function renderParamInput(param) {
  const id = `form-param-${param.key}`;
  const defVal = param.default;
  const label = param.label || param.key;

  if (param.type === 'bool' || param.type === 'boolean') {
    return `
      <div class="form-group">
        <label class="inline-flex items-center gap-2 cursor-pointer">
          <input type="checkbox" class="form-checkbox" id="${id}" ${defVal ? 'checked' : ''}>
          <span class="text-sm text-gray-700">${escapeHtml(label)}</span>
        </label>
      </div>`;
  }

  if (param.type === 'select') {
    return `
      <div class="form-group">
        <label class="form-label" for="${id}">${escapeHtml(label)}</label>
        <select class="form-select" id="${id}">
          ${(param.options || []).map(opt => `
            <option value="${escapeHtml(opt)}" ${opt === String(defVal) ? 'selected' : ''}>${escapeHtml(opt)}</option>
          `).join('')}
        </select>
      </div>`;
  }

  if (param.type === 'fixed') {
    return `
      <div class="form-group">
        <label class="form-label">${escapeHtml(label)}</label>
        <input type="text" class="form-input bg-gray-100" value="${escapeHtml(String(defVal))}" readonly>
      </div>`;
  }

  // Default: number or string
  const isNum = param.type === 'number';
  return `
    <div class="form-group">
      <label class="form-label" for="${id}">${escapeHtml(label)}</label>
      <input type="${isNum ? 'number' : 'text'}" class="form-input" id="${id}"
        placeholder="${escapeHtml(String(defVal != null ? defVal : ''))}"
        value="${defVal != null ? escapeHtml(String(defVal)) : ''}">
    </div>`;
}

function renderSweepParams(label, paramName) {
  return `
    <div class="mb-4 p-4 bg-amber-50/50 rounded-lg border border-amber-100">
      <h4 class="text-sm font-semibold text-amber-900 mb-3">🔁 扫描参数: ${escapeHtml(label)}</h4>
      <div class="flex flex-wrap items-center gap-2" id="sweep-tags">
        ${formState.sweepValues.map((v, i) => `
          <span class="tag">${escapeHtml(String(v))}
            <span class="tag-remove" onclick="window.removeSweepValue(${i})" title="移除">&times;</span>
          </span>
        `).join('')}
      </div>
      <div class="flex items-center gap-2 mt-3">
        <input type="number" class="form-input w-24" id="sweep-new-value" placeholder="值" min="1">
        <button class="btn btn-secondary btn-sm" onclick="window.addSweepValue()" type="button">
          ${iconSvg('plus', 14)} 添加
        </button>
      </div>
    </div>
  `;
}

// ── Sweep Value Handlers ─────────────────────────────────────────────
window.addSweepValue = () => {
  const inp = document.getElementById('sweep-new-value');
  if (!inp || !inp.value) return;
  const v = Number(inp.value);
  if (isNaN(v) || v <= 0) { showToast('请输入有效的正整数值', 'warning'); return; }
  if (formState.sweepValues.includes(v)) { showToast('该值已存在', 'warning'); return; }
  formState.sweepValues.push(v);
  formState.sweepValues.sort((a, b) => a - b);
  inp.value = '';
  rerenderForm();
};

window.removeSweepValue = (i) => {
  formState.sweepValues.splice(i, 1);
  rerenderForm();
};

// ── Category & Type Selection ────────────────────────────────────────
window.selectCat = (cat) => {
  formState.selectedCategory = cat;
  formState.selectedType = null;
  rerenderForm();
};

window.selectTestType = (typeName) => {
  const types = formState.testTypes || [];
  formState.selectedType = types.find(t => t.type === typeName) || null;
  if (formState.selectedType) {
    formState.sweepValues = [...(formState.selectedType.default_sweep_values || [])];
  }
  rerenderForm();
};

// ── Re-render ────────────────────────────────────────────────────────
function rerenderForm() {
  const c = document.getElementById('test-form-container');
  if (!c) return;
  c.innerHTML = renderTestTypeCards() + renderTestForm();
  updateSweepHint();
}

function updateSweepHint() {
  const hint = document.getElementById('form-subtask-hint');
  if (!hint) return;
  const hasSweep = formState.selectedType && !!formState.selectedType.sweep_config;
  hint.innerHTML = hasSweep
    ? `将生成 <strong>${formState.sweepValues.length}</strong> 个子任务`
    : '将生成 1 个子任务';
}

// ── Submit ───────────────────────────────────────────────────────────
window.submitTest = async () => {
  const t = formState.selectedType;
  if (!t) { showToast('请先选择测试类型', 'warning'); return; }

  // Collect form data
  const formData = {};
  const form = document.getElementById('test-form-container');
  if (!form) return;

  // Text/number/select inputs (skip sweep-new-value)
  form.querySelectorAll('input[type="text"], input[type="number"], select').forEach(el => {
    if (el.id && el.id !== 'sweep-new-value') {
      const key = el.id.replace('form-param-', '').replace('form-', '');
      formData[key] = el.value;
    }
  });
  // Checkboxes
  form.querySelectorAll('input[type="checkbox"]').forEach(el => {
    if (el.id) {
      const key = el.id.replace('form-param-', '').replace('form-', '');
      formData[key] = el.checked;
    }
  });

  // Build fixed_params from all param definitions
  const allDefs = [...(t.fixed_params || [])];
  const fixedParams = {};
  for (const p of allDefs) {
    const key = p.key;
    let val = formData[key];
    if (val === undefined || val === '') {
      // Use default
      val = p.default;
    }
    if (val === undefined || val === '' || val === null) continue;

    if (p.type === 'bool' || p.type === 'boolean') {
      val = val === true || val === 'true';
    } else if (p.type === 'number') {
      val = Number(val);
    }
    fixedParams[key] = val;
  }

  // Also include sweep_key value (will be set per-subtask by backend)
  const hasSweep = !!t.sweep_config && formState.sweepValues.length > 0;

  const payload = {
    test_type: t.type,
    fixed_params: fixedParams,
    ...(hasSweep ? {
      sweep_key: t.sweep_config.key,
      sweep_values: formState.sweepValues,
    } : {}),
  };

  // Test name
  const nameEl = document.getElementById('form-test-name');
  if (nameEl && nameEl.value.trim()) {
    payload.name = nameEl.value.trim();
  }

  const btn = document.getElementById('form-submit-btn');
  if (btn) {
    btn.disabled = true;
    btn.textContent = '提交中...';
  }

  try {
    const result = await createTest(payload);
    showToast('测试已创建并开始运行', 'success');
    const testId = result.id;
    if (testId) {
      setTimeout(() => navigate(`/tests/${testId}`), 500);
    }
  } catch (err) {
    showToast('提交失败: ' + err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = '🚀 提交测试';
    }
  }
};

// ── Main Export ──────────────────────────────────────────────────────
export async function renderNewTestPage() {
  if (!formState.testTypes) {
    try {
      formState.testTypes = await getTestTypes();
    } catch (err) {
      return `
        <div class="text-center py-16">
          <div class="text-4xl mb-4">⚠️</div>
          <h2 class="text-xl font-bold text-gray-700 mb-2">无法连接后端服务</h2>
          <p class="text-gray-500 mb-4">${escapeHtml(err.message)}</p>
          <p class="text-sm text-gray-400">请确保后端运行在 http://localhost:8001</p>
          <button class="btn btn-primary mt-4" onclick="location.reload()">🔄 重试</button>
        </div>`;
    }
  }

  formState.selectedType = null;
  formState.selectedCategory = null;
  formState.sweepValues = [];

  return `
    <div>
      <h2 class="text-xl font-bold text-gray-800 mb-2 flex items-center gap-2">
        ${iconSvg('zap', 22)} 新建测试
      </h2>
      <p class="text-sm text-gray-500 mb-6">选择测试类型并配置参数，开始性能压测</p>
      <div id="test-form-container">
        ${renderTestTypeCards()}
      </div>
    </div>`;
}
