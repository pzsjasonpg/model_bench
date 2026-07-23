/**
 * Main application entry point
 * Hash-based router for the model benchmark testing platform
 */
import { parseRoute } from './utils.js';
import { renderLayout } from './components/layout.js';

// Page modules
import * as newTestPage from './pages/new-test.js';
import * as testListPage from './pages/test-list.js';
import * as testDetailPage from './pages/test-detail.js';

let currentPage = null;

const pageMap = {
  'new-test': newTestPage,
  'test-list': testListPage,
  'test-detail': testDetailPage,
};

async function router() {
  const route = parseRoute();
  const page = pageMap[route.page];

  if (!page) {
    const html = await newTestPage.render();
    renderApp(html);
    currentPage = newTestPage;
    return;
  }

  // Cleanup previous page
  if (currentPage && currentPage !== page && currentPage.cleanup) {
    currentPage.cleanup();
  }

  // Render new page
  const html = await page.render(route.params);
  renderApp(html);

  // Post-render init (e.g., log viewer WebSocket, event bindings)
  if (page.init) {
    setTimeout(() => page.init(), 0);
  }

  currentPage = page;
}

function renderApp(contentHtml) {
  const app = document.getElementById('app');
  if (!app) return;

  const layoutHtml = renderLayout(contentHtml);
  app.innerHTML = layoutHtml;

  // Tag the main content area so sub-components can update it dynamically
  const mainEl = app.querySelector('main');
  if (mainEl) {
    mainEl.id = 'app-content';
  }
}

window.addEventListener('hashchange', router);

document.addEventListener('DOMContentLoaded', () => {
  if (!window.location.hash || window.location.hash === '#') {
    window.location.hash = '#/';
  }
  router();
});

// Cleanup on visibility change
document.addEventListener('visibilitychange', () => {
  if (document.hidden && currentPage && currentPage.cleanup) {
    currentPage.cleanup();
  } else if (!document.hidden) {
    router();
  }
});
