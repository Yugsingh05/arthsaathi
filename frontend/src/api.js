const j = async (url, opts) => {
  const r = await fetch(url, opts)
  if (!r.ok) throw new Error(`${r.status} ${url}`)
  return r.json()
}
const post = (url, body) =>
  j(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const api = {
  meta: (lang = 'en') => j(`/api/meta?lang=${lang}`),
  customers: (q = '', lang = 'en') => j(`/api/customers?q=${encodeURIComponent(q)}&lang=${lang}`),
  customer: (id, asOf, lang) => j(`/api/customer/${id}?as_of=${asOf}&lang=${lang}`),
  transactions: (id, asOf, lang = 'en') => j(`/api/customer/${id}/transactions?as_of=${asOf}&limit=25&lang=${lang}`),
  timeline: (id, asOf, lang = 'en') => j(`/api/customer/${id}/timeline?as_of=${asOf}&lang=${lang}`),
  ledger: (id) => j(`/api/customer/${id}/ledger`),
  setConsent: (id, purpose, granted) => post(`/api/customer/${id}/consent`, { purpose, granted }),
  intervention: (customer_id, action, as_of) => post('/api/intervention', { customer_id, action, as_of }),
  assistantStart: (b) => post('/api/assistant/start', b),
  assistantReply: (session_id, text) => post('/api/assistant/reply', { session_id, text }),
  exposures: () => j('/api/exposures'),
  exposureCases: () => j('/api/exposures/cases'),
  queue: (asOf, lang = 'en') => j(`/api/staff/queue?as_of=${asOf}&limit=50&lang=${lang}`),
  fairness: (asOf) => j(`/api/staff/fairness?as_of=${asOf}`),
  override: (customer_id, decision, note) => post('/api/staff/override', { customer_id, decision, note }),
}
