/**
 * API client for model benchmark backend
 */

const BASE_URL = 'http://localhost:38081';
const WS_BASE = 'ws://localhost:38081';

/**
 * Generic fetch wrapper with error handling
 */
async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  let response;
  try {
    response = await fetch(url, config);
  } catch (err) {
    throw new Error(`Network error: ${err.message}`);
  }

  if (!response.ok) {
    let detail = '';
    try {
      const errData = await response.json();
      detail = errData.detail || errData.message || '';
    } catch (_) { /* ignore */ }
    throw new Error(detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

/**
 * GET request
 */
function get(path, params = {}) {
  const searchParams = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val != null && val !== '') {
      searchParams.set(key, String(val));
    }
  }
  const query = searchParams.toString();
  const fullPath = query ? `${path}?${query}` : path;
  return request(fullPath, { method: 'GET' });
}

/**
 * POST request
 */
function post(path, body = {}) {
  return request(path, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * DELETE request
 */
function del(path) {
  return request(path, { method: 'DELETE' });
}

// ==================== API functions ====================

/**
 * Create and start a test
 */
export async function createTest(payload) {
  return post('/api/tests', payload);
}

/**
 * List tests with optional filters
 */
export async function listTests(params = {}) {
  return get('/api/tests', params);
}

/**
 * Get test detail with subtasks
 */
export async function getTest(id) {
  return get(`/api/tests/${id}`);
}

/**
 * Stop a running test
 */
export async function stopTest(id) {
  return post(`/api/tests/${id}/stop`);
}

/**
 * Delete a test
 */
export async function deleteTest(id) {
  return del(`/api/tests/${id}`);
}

/**
 * Get logs for a test
 */
export async function getTestLogs(id, params = {}) {
  return get(`/api/tests/${id}/logs`, params);
}

/**
 * Get aggregated result for a test
 */
export async function getTestResult(id) {
  return get(`/api/tests/${id}/result`);
}

/**
 * Get all test type schemas
 */
let testTypesCache = null;
export async function getTestTypes() {
  if (testTypesCache) return testTypesCache;
  testTypesCache = await get('/api/test-types');
  return testTypesCache;
}

/**
 * Clear test types cache
 */
export function clearTestTypesCache() {
  testTypesCache = null;
}

/**
 * Browse data files
 */
export async function browseDataFiles(path = '') {
  const params = path ? { path } : {};
  return get('/api/data/files', params);
}

/**
 * Create WebSocket connection for real-time logs
 */
export function createLogWebSocket(testId) {
  const url = `${WS_BASE}/ws/tests/${testId}`;
  const ws = new WebSocket(url);
  return ws;
}
