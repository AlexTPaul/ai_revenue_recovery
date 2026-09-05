const BASE_URL = '/api';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      errorDetail = `${response.status} ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Batch
  runBatch: (caseCount = 15) =>
    request('/batch/run', {
      method: 'POST',
      body: JSON.stringify({ case_count: caseCount }),
    }),

  getSummary: () => request('/batch/summary'),

  resetBatch: () =>
    request('/batch/reset', {
      method: 'POST',
    }),

  // Cases
  getCases: (params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.failure_reason) query.append('failure_reason', params.failure_reason);
    const queryString = query.toString() ? `?${query.toString()}` : '';
    return request(`/cases${queryString}`);
  },

  getCaseDetail: (attemptId) => request(`/cases/${attemptId}`),

  getCaseAudit: (attemptId) => request(`/cases/${attemptId}/audit`),

  // Virtual Clock
  getClock: () => request('/clock'),

  fastForwardClock: (days = 1, hours = 0) =>
    request('/clock/fast-forward', {
      method: 'POST',
      body: JSON.stringify({ days, hours }),
    }),

  resetClock: () =>
    request('/clock/reset', {
      method: 'POST',
    }),

  // Chat (Promise-to-Pay)
  sendMessage: (promiseId, message) =>
    request('/chat/message', {
      method: 'POST',
      body: JSON.stringify({ promise_id: promiseId, message }),
    }),

  getChatHistory: (promiseId) => request(`/chat/${promiseId}/history`),

  // Escalation Queue
  getEscalationQueue: () => request('/escalation/queue'),

  resolveEscalation: (caseId, payload) =>
    request(`/escalation/${caseId}/resolve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Webhook Simulator
  simulateRazorpayWebhook: (payload, signature = null) =>
    request('/webhooks/razorpay', {
      method: 'POST',
      headers: signature ? { 'X-Razorpay-Signature': signature } : {},
      body: JSON.stringify(payload),
    }),
};
