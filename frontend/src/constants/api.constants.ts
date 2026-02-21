/**
 * API Configuration
 *
 * BASE_URL  – swap to the real backend origin before going to production.
 * All endpoint helpers are pure functions so path params stay type-safe.
 */

export const BASE_URL = 'https://api.digitalevidencegap.com/v1';

export const API_ENDPOINTS = {
  // ── Cases ────────────────────────────────────────────────────────────────
  CASES: {
    /** GET  /cases  – list all cases */
    GET_ALL: '/cases',

    /** GET  /cases/:id  – single case detail */
    GET_BY_ID: (id: string) => `/cases/${id}`,

    /** POST /cases  – create a new case */
    CREATE: '/cases',

    /** PUT  /cases/:id  – update an existing case */
    UPDATE: (id: string) => `/cases/${id}`,

    /** DELETE /cases/:id  – delete a case */
    DELETE: (id: string) => `/cases/${id}`,
  },

  // ── Chat / Messages ───────────────────────────────────────────────────────
  CHAT: {
    /** GET  /cases/:caseId/messages  – fetch conversation history */
    GET_MESSAGES: (caseId: string) => `/cases/${caseId}/messages`,

    /** POST /cases/:caseId/messages  – send a new message */
    SEND_MESSAGE: (caseId: string) => `/cases/${caseId}/messages`,
  },

  // ── Evidence Files ────────────────────────────────────────────────────────
  EVIDENCE: {
    /** GET  /cases/:caseId/evidence  – list all evidence files for a case */
    GET_ALL: (caseId: string) => `/cases/${caseId}/evidence`,

    /** POST /cases/:caseId/evidence  – upload a new evidence file */
    UPLOAD: (caseId: string) => `/cases/${caseId}/evidence`,

    /** DELETE /cases/:caseId/evidence/:evidenceId  – remove an evidence file */
    DELETE: (caseId: string, evidenceId: string) =>
      `/cases/${caseId}/evidence/${evidenceId}`,
  },
} as const;
