import { useEffect, useRef, useState } from 'react'
import { Panel, Pill, cx, inr, pct } from '../components/ui'
import { api } from '../api'

const STEPS = {
  loan: ['purpose', 'amount', 'tenure', 'affordability', 'pan', 'aadhaar_consent', 'kfs', 'done'],
  // language is not asked here: the header already sets it
  onboarding: ['mobile', 'otp', 'pan', 'purpose_consent', 'done'],
}
const REGULATED = ['pan', 'aadhaar_consent', 'purpose_consent', 'kfs', 'affordability']

// A halt is the affordability check refusing to go on, so the tracker should
// stop there rather than fall off the list.
const HALT_AT = { stress_stop: 'affordability' }

function KfsCard({ kfs, t }) {
  const figures = [
    [t('kfs_borrow'), inr(kfs.amount)],
    [t('kfs_monthly'), `${inr(kfs.emi)} × ${kfs.months}`],
    [t('kfs_interest'), `${kfs.rate}% p.a.`],
    ['APR', `${kfs.apr}%`],
    [t('kfs_processing'), inr(kfs.processing_fee)],
    [t('kfs_total'), inr(kfs.total_repayable)],
  ]
  return (
    <div className="mt-2.5 overflow-hidden rounded-lg border border-[#e6e8ef] bg-white">
      <p className="border-b border-[#eef0f5] bg-[#fafbfd] px-3 py-2 text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[#8a93a8]">
        {t('journey_step_kfs')}
      </p>
      <dl className="divide-y divide-[#f0f2f7]">
        {figures.map(([k, v]) => (
          <div key={k} className="flex items-baseline justify-between gap-3 px-3 py-1.5">
            <dt className="text-[12px] text-[#77809a]">{k}</dt>
            <dd className="tnum text-[12.5px] font-semibold text-[#1b2333]">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="border-t border-[#eef0f5] px-3 py-2 text-[11.5px] leading-relaxed text-[#77809a]">
        {kfs.prepayment}
      </p>
    </div>
  )
}

export default function Journeys({ customerId, lang, asOf, t }) {
  const [flow, setFlow] = useState('loan')
  const [state, setState] = useState(null)
  const [msgs, setMsgs] = useState([])
  const [input, setInput] = useState('')
  const [listening, setListening] = useState(false)
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(null)
  const endRef = useRef(null)

  const push = (who, text, meta) => {
    // a step can carry a card with no sentence of its own; an empty bubble is
    // never worth rendering
    if (!text && !meta?.kfs) return
    setMsgs((m) => [...m, { who, text, meta }])
  }

  const begin = async (f) => {
    setFlow(f); setMsgs([]); setState(null); setInput(''); setFailed(null); setBusy(true)
    try {
      const s = await api.assistantStart({ customer_id: customerId, flow: f, lang, as_of: asOf })
      setState(s)
      push('bot', s.message, s)
    } catch {
      setFailed(t('journey_unavailable'))
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => { begin('loan') }, [customerId, lang, asOf])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) }, [msgs])

  const done = Boolean(state?.done)

  const send = async (text) => {
    if (!text?.trim() || !state?.session_id || done || busy) return
    push('me', text)
    setInput('')
    setBusy(true)
    try {
      const s = await api.assistantReply(state.session_id, text)
      setState(s)
      push('bot', s.message, s)
    } catch {
      setFailed(t('journey_unavailable'))
    } finally {
      setBusy(false)
    }
  }

  const mic = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    const r = new SR()
    r.lang = { hi: 'hi-IN', gu: 'gu-IN', en: 'en-IN' }[lang] || 'en-IN'
    r.onstart = () => setListening(true)
    r.onend = () => setListening(false)
    r.onerror = () => setListening(false)
    r.onresult = (e) => send(e.results[0][0].transcript)
    r.start()
  }

  const steps = STEPS[flow]
  const marker = HALT_AT[state?.step] || state?.step
  const idx = done && !state?.halted ? steps.length - 1 : steps.indexOf(marker)
  const canType = Boolean(state?.session_id) && !done && !busy

  return (
    <div className="grid gap-5 lg:grid-cols-[1.25fr_1fr]">
      <Panel title={t('conversation')} bodyClass=""
        subtitle={t('conversation_sub')}
        action={
          <div className="flex gap-1 rounded-lg bg-[#f1f3f8] p-0.5">
            {['loan', 'onboarding'].map((f) => (
              <button key={f} onClick={() => begin(f)}
                className={cx('rounded-md px-2.5 py-1 text-[12px] font-semibold transition-colors',
                  flow === f ? 'bg-white text-[#14306b] shadow-sm' : 'text-[#77809a] hover:text-[#14306b]')}>
                {t(f === 'loan' ? 'flow_loan' : 'flow_onboarding')}</button>
            ))}
          </div>
        }>
        <div className="flex h-[480px] flex-col">
          <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
            {msgs.map((m, i) => (
              <div key={i} className={cx('flex', m.who === 'me' ? 'justify-end' : 'justify-start')}>
                <div className={cx('max-w-[82%] rounded-xl px-3.5 py-2.5 text-[13px] leading-relaxed',
                  m.who === 'me' ? 'bg-[#14306b] text-white'
                    : m.meta?.error ? 'bg-amber-50 text-[#7a5b12]'
                      : 'bg-[#f4f6fa] text-[#1b2333]')}>
                  {m.text && <span lang={lang}>{m.text}</span>}
                  {m.meta?.mandatory && <div className="mt-2"><Pill tone="blue">{m.meta.mandatory}</Pill></div>}
                  {m.meta?.note && <p className="mt-1.5 text-[12px] text-[#77809a]">{m.meta.note}</p>}
                  {m.meta?.halted && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {m.meta.offer?.map((o) => <Pill key={o} tone="amber">{o.replace(/_/g, ' ')}</Pill>)}
                    </div>
                  )}
                  {m.meta?.kfs && <KfsCard kfs={m.meta.kfs} t={t} />}
                </div>
              </div>
            ))}

            {!done && state?.choices?.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {state.choices.map((c) => (
                  <button key={c.id} onClick={() => send(c.id)} lang={lang} disabled={busy}
                    className="rounded-full border border-[#dfe3ec] bg-white px-3 py-1.5 text-[12.5px] font-medium text-[#14306b] transition-colors hover:border-[#14306b]/40 disabled:opacity-50">
                    {c.label}
                  </button>
                ))}
              </div>
            )}

            {!done && state?.kind === 'consent' && (
              <div className="flex gap-1.5">
                {[['yes', t('yes')], ['no', t('no')]].map(([v, label]) => (
                  <button key={v} onClick={() => send(v)} disabled={busy}
                    className="rounded-full border border-[#dfe3ec] bg-white px-4 py-1.5 text-[12.5px] font-semibold text-[#14306b] transition-colors hover:border-[#14306b]/40 disabled:opacity-50">
                    {label}
                  </button>
                ))}
              </div>
            )}

            {done && (
              <div className="flex items-center gap-2 pt-1">
                <Pill tone={state?.halted ? 'amber' : 'green'}>
                  {state?.halted ? t('journey_halted_pill') : t('journey_complete')}
                </Pill>
                <button onClick={() => begin(flow)}
                  className="rounded-full border border-[#dfe3ec] bg-white px-3 py-1.5 text-[12px] font-semibold text-[#14306b] transition-colors hover:border-[#14306b]/40">
                  {t('start_again')}
                </button>
              </div>
            )}

            {failed && <p className="text-[12.5px] text-red-600">{failed}</p>}
            <div ref={endRef} />
          </div>

          <div className="flex items-center gap-2 border-t border-[#eef0f5] px-4 py-3">
            <button onClick={mic} title={t('voice_input')} disabled={!canType}
              className={cx('grid h-8 w-8 shrink-0 place-items-center rounded-lg text-[14px] disabled:opacity-40',
                listening ? 'animate-pulse bg-red-500 text-white' : 'bg-[#f1f3f8]')}>🎤</button>
            <input id="journey-input" value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send(input)} disabled={!canType}
              placeholder={done ? t('journey_closed') : t('type_reply')}
              className="min-w-0 flex-1 rounded-lg bg-[#f1f3f8] px-3 py-2 text-[13px] outline-none disabled:text-[#a3aabb]" />
            <button onClick={() => send(input)} disabled={!canType || !input.trim()}
              className="shrink-0 rounded-lg bg-[#14306b] px-3.5 py-2 text-[12.5px] font-semibold text-white transition-opacity disabled:opacity-40">
              {t('send')}
            </button>
          </div>
        </div>
      </Panel>

      <div className="space-y-5">
        <Panel title={t('regulated_script')} subtitle={t('regulated_sub')}>
          <ol className="space-y-0">
            {steps.map((s, i) => {
              const complete = i < idx || (done && !state?.halted)
              const current = i === idx && !complete
              return (
                <li key={s} className={cx('flex items-center gap-3 rounded-lg px-2 py-2',
                  current && 'bg-[#14306b]/5')}>
                  <span className={cx('grid h-6 w-6 shrink-0 place-items-center rounded-full text-[11px] font-semibold',
                    complete ? 'bg-emerald-500 text-white'
                      : current ? 'bg-[#14306b] text-white'
                        : 'bg-[#eceef4] text-[#8a93a8]')}>
                    {complete ? '✓' : i + 1}
                  </span>
                  <span className={cx('flex-1 text-[13px] capitalize',
                    current ? 'font-semibold text-[#14306b]' : 'text-[#4a5468]')}>
                    {t(`journey_step_${s}`)}
                  </span>
                  {REGULATED.includes(s) && <Pill tone="blue">{t('required')}</Pill>}
                </li>
              )
            })}
          </ol>
        </Panel>

        {state?.halted && (
          <Panel title={t('journey_stopped')}>
            <p className="text-[13px] leading-relaxed text-[#4a5468]">
              {t('journey_halt_detail', { score: pct(state.stress?.score) })}
            </p>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {state.stress?.fired.map((f) => <Pill key={f.code} tone="amber">{f.code}</Pill>)}
            </div>
            <p className="mt-3 text-[12px] text-[#77809a]">
              {t('journey_halt_audit')}
            </p>
          </Panel>
        )}
      </div>
    </div>
  )
}
