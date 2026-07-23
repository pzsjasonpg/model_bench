/**
 * New Test Page
 */
import { renderNewTestPage as renderForm } from '../components/test-form.js';

export async function render() {
  return await renderForm();
}

export function cleanup() {
  // No cleanup needed
}
