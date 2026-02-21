/**
 * ChatWorkspace Service
 *
 * Wraps all chat-message and evidence-file API calls.
 * Currently returns static demo data so the UI works without a real backend.
 *
 * When the real API is ready:
 *   1. Remove the demo-data imports.
 *   2. Replace each function body with a real `fetch` / axios call.
 *   3. Keep the same return-type signatures — components need zero changes.
 */

import { BASE_URL, API_ENDPOINTS } from '../constants/api.constants';
import { getCaseById } from './cases.service';
import {
  DEMO_TRAFFIC_MESSAGES,
  DEMO_INTERSECTION_MESSAGES,
  DEFAULT_MESSAGES,
  MOCK_EVIDENCE_FILES,
  CASE_META,
  DEFAULT_CASE_META,
  type Message,
  type EvidenceFile,
} from '../constants/chatWorkspace.constants';

// ── Shared response wrapper ──────────────────────────────────────────────────

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

// ── Types re-exported for convenience ────────────────────────────────────────

export type { Message, EvidenceFile };

export interface CaseMeta {
  title: string;
  evidenceCount: string;
}

// ─── GET /cases/:caseId/messages ─────────────────────────────────────────────

/**
 * Fetch the conversation history for a given case.
 *
 * Demo behaviour: returns pre-seeded message arrays keyed by case ID.
 *
 * Real API endpoint: GET ${BASE_URL}${API_ENDPOINTS.CHAT.GET_MESSAGES(caseId)}
 */
export async function getMessages(caseId: string): Promise<ApiResponse<Message[]>> {
  // TODO: replace with →
  //   const res = await fetch(`${BASE_URL}${API_ENDPOINTS.CHAT.GET_MESSAGES(caseId)}`);
  //   const json = await res.json();
  //   return { data: json.messages, success: res.ok };
  console.debug(
    '[ChatService] GET',
    `${BASE_URL}${API_ENDPOINTS.CHAT.GET_MESSAGES(caseId)}`
  );

  const messageMap: Record<string, Message[]> = {
    'demo-traffic-case': DEMO_TRAFFIC_MESSAGES,
    'demo-intersection-case': DEMO_INTERSECTION_MESSAGES,
  };

  const messages = messageMap[caseId] ?? DEFAULT_MESSAGES;
  return { data: messages, success: true };
}

// ─── POST /cases/:caseId/messages ────────────────────────────────────────────

export interface SendMessagePayload {
  content: string;
}

/**
 * Send a user message and receive the AI reply.
 *
 * Real API endpoint: POST ${BASE_URL}${API_ENDPOINTS.CHAT.SEND_MESSAGE(caseId)}
 */
export async function sendMessage(
  caseId: string,
  payload: SendMessagePayload
): Promise<ApiResponse<Message>> {
  // TODO: replace with →
  //   const res = await fetch(`${BASE_URL}${API_ENDPOINTS.CHAT.SEND_MESSAGE(caseId)}`, {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify(payload),
  //   });
  console.debug(
    '[ChatService] POST',
    `${BASE_URL}${API_ENDPOINTS.CHAT.SEND_MESSAGE(caseId)}`,
    payload
  );

  const userMessage: Message = {
    id: Date.now().toString(),
    type: 'user',
    content: payload.content,
    timestamp: new Date().toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    }),
  };

  return { data: userMessage, success: true };
}

// ─── GET /cases/:caseId/evidence ─────────────────────────────────────────────

/**
 * Fetch the list of evidence files for a case.
 *
 * Real API endpoint: GET ${BASE_URL}${API_ENDPOINTS.EVIDENCE.GET_ALL(caseId)}
 */
export async function getEvidenceFiles(
  caseId: string
): Promise<ApiResponse<EvidenceFile[]>> {
  // TODO: replace with →
  //   const res = await fetch(`${BASE_URL}${API_ENDPOINTS.EVIDENCE.GET_ALL(caseId)}`);
  console.debug(
    '[ChatService] GET',
    `${BASE_URL}${API_ENDPOINTS.EVIDENCE.GET_ALL(caseId)}`
  );

  // Demo: return the same mock evidence list for every case
  return { data: MOCK_EVIDENCE_FILES, success: true };
}

// ─── DELETE /cases/:caseId/evidence/:evidenceId ───────────────────────────────

/**
 * Delete a single evidence file.
 *
 * Real API endpoint: DELETE ${BASE_URL}${API_ENDPOINTS.EVIDENCE.DELETE(caseId, evidenceId)}
 */
export async function deleteEvidenceFile(
  caseId: string,
  evidenceId: string
): Promise<ApiResponse<null>> {
  // TODO: replace with →
  //   const res = await fetch(
  //     `${BASE_URL}${API_ENDPOINTS.EVIDENCE.DELETE(caseId, evidenceId)}`,
  //     { method: 'DELETE' }
  //   );
  console.debug(
    '[ChatService] DELETE',
    `${BASE_URL}${API_ENDPOINTS.EVIDENCE.DELETE(caseId, evidenceId)}`
  );

  return { data: null, success: true };
}

// ─── GET case metadata (title + evidence count) ───────────────────────────────

/**
 * Resolve display metadata for a case (title, evidence count label).
 *
 * This would typically come from the case detail endpoint in production.
 */
export async function getCaseMeta(caseId: string): Promise<ApiResponse<CaseMeta>> {
  console.debug('[ChatService] getCaseMeta', caseId);

  // Try to find the real case first
  const realCaseRes = await getCaseById(caseId);
  if (realCaseRes.success && realCaseRes.data) {
    return {
      data: {
        title: realCaseRes.data.title,
        evidenceCount: `${realCaseRes.data.mediaCount} analyzed`,
      },
      success: true,
    };
  }

  // Fallback to constants for hardcoded demos if not found
  const meta = CASE_META[caseId] ?? DEFAULT_CASE_META;
  return { data: meta, success: true };
}
