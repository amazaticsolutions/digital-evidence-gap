/**
 * Cases Service
 *
 * Wraps all case-related API calls.  Currently returns static demo data so the
 * UI works end-to-end without a real backend.
 *
 * When the real API is ready:
 *   1. Remove the demo-data imports at the top.
 *   2. Replace each function body with a real `fetch` / axios call using the
 *      endpoint constants from `api.constants.ts`.
 *   3. Keep the same return-type signatures so the components need zero changes.
 */

import { BASE_URL, API_ENDPOINTS } from '../constants/api.constants';
import {
  DEMO_CASE,
  ADDITIONAL_DEMO_CASES,
  type DemoCase as Case,
} from '../constants/pastCases.constants';

// ── Shared response wrapper ──────────────────────────────────────────────────

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

// ─── GET /cases ──────────────────────────────────────────────────────────────

/**
 * Fetch all cases.
 *
 * Demo behaviour: merges user-created cases from localStorage with the seeded
 * demo cases, mirroring what the real endpoint would return.
 *
 * Real API endpoint: GET ${BASE_URL}${API_ENDPOINTS.CASES.GET_ALL}
 */
export async function getCases(): Promise<ApiResponse<Case[]>> {
  // TODO: replace with → const res = await fetch(`${BASE_URL}${API_ENDPOINTS.CASES.GET_ALL}`);
  console.debug('[CasesService] GET', `${BASE_URL}${API_ENDPOINTS.CASES.GET_ALL}`);

  const storedCases: Case[] = JSON.parse(localStorage.getItem('cases') || '[]');
  const hasDemoCase = storedCases.some((c) => c.id === DEMO_CASE.id);

  const allCases = hasDemoCase
    ? storedCases
    : [...storedCases, ...ADDITIONAL_DEMO_CASES, DEMO_CASE];

  return { data: allCases, success: true };
}

// ─── GET /cases/:id ──────────────────────────────────────────────────────────

/**
 * Fetch a single case by ID.
 *
 * Real API endpoint: GET ${BASE_URL}${API_ENDPOINTS.CASES.GET_BY_ID(id)}
 */
export async function getCaseById(id: string): Promise<ApiResponse<Case | null>> {
  // TODO: replace with → const res = await fetch(`${BASE_URL}${API_ENDPOINTS.CASES.GET_BY_ID(id)}`);
  console.debug('[CasesService] GET', `${BASE_URL}${API_ENDPOINTS.CASES.GET_BY_ID(id)}`);

  const { data: cases } = await getCases();
  const found = cases.find((c) => c.id === id) ?? null;

  return { data: found, success: !!found };
}

// ─── POST /cases ─────────────────────────────────────────────────────────────

export interface CreateCasePayload {
  title: string;
  description: string;
  mediaCount: number;
  uploadProgress: number;
}

/**
 * Create a new case and persist it locally (demo: localStorage).
 *
 * Real API endpoint: POST ${BASE_URL}${API_ENDPOINTS.CASES.CREATE}
 */
export async function createCase(
  payload: CreateCasePayload
): Promise<ApiResponse<Case>> {
  // TODO: replace with →
  //   const res = await fetch(`${BASE_URL}${API_ENDPOINTS.CASES.CREATE}`, {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify(payload),
  //   });
  console.debug('[CasesService] POST', `${BASE_URL}${API_ENDPOINTS.CASES.CREATE}`, payload);

  const newCase: Case = {
    id: Math.random().toString(36).substr(2, 9),
    title: payload.title,
    description: payload.description,
    mediaCount: payload.mediaCount,
    uploadProgress: payload.uploadProgress,
    status: payload.uploadProgress === 100 ? 'completed' : 'processing',
    createdAt: new Date().toISOString(),
  };

  const existing: Case[] = JSON.parse(localStorage.getItem('cases') || '[]');
  localStorage.setItem('cases', JSON.stringify([newCase, ...existing]));

  return { data: newCase, success: true };
}

// ─── DELETE /cases/:id ───────────────────────────────────────────────────────

/**
 * Delete a case by ID.
 *
 * Real API endpoint: DELETE ${BASE_URL}${API_ENDPOINTS.CASES.DELETE(id)}
 */
export async function deleteCase(id: string): Promise<ApiResponse<null>> {
  // TODO: replace with →
  //   const res = await fetch(`${BASE_URL}${API_ENDPOINTS.CASES.DELETE(id)}`, { method: 'DELETE' });
  console.debug('[CasesService] DELETE', `${BASE_URL}${API_ENDPOINTS.CASES.DELETE(id)}`);

  const existing: Case[] = JSON.parse(localStorage.getItem('cases') || '[]');
  localStorage.setItem('cases', JSON.stringify(existing.filter((c) => c.id !== id)));

  return { data: null, success: true };
}
