import { useEffect, useRef, useState } from 'react'
import { Panel, Pill, cx } from '../components/ui'
import { api } from '../api'

const STEPS = {
  loan: ['purpose', 'amount', 'tenure', 'affordability', 'pan', 'aadhaar_consent', 'kfs', 'done'],
  onboarding: ['language', 'mobile', 'otp', 'pan', 'purpose_consent', 'done'],
}
const REGULATED = ['pan', 'aadhaar_consent', 'purpose_consent', 'kfs', 'affordability']

export default function Journeys({ customerId, lang, asOf, t }) {
  const [flow, setFlow] = useState('loan')
  const [state, setState] = useState(null)
  const [msgs, setMsgs] = useState([])
  const [input, setInput] = useState('')
  const [listening, setListening] = useState(false)
  const endRef = useRef(null)

  const begin = async (f) => {
    setFlow(f); setMsgs([])
    const s = await api.assistantStart({ customer_id: customerId, flow: f, lang, as_of: asOf })
    setState(s); setMsgs([{ who: 'bot', text: s.message, meta: s }])
  }

  useEffect(() => { begin('loan') }, [customerId, lang, asOf])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) }, [msgs])

  const send = async (text) => {
    if (!text?.trim() || !state?.session_id) return
    setMsgs((m) => [...m, { who: 'me', text }])
    setInput('')
    const s = await api.assistantReply(state.session_id, text)
    setState(s)
    setMsgs((m) => [...m, { who: 'bot', text: s.message, meta: s }])
  }

  const mic = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    const r = new SR()
    r.lang = { hi: 'hi-IN', gu: 'gu-IN', en: 'en-IN' }[lang] || 'en-IN'
    r.onstart = () => setListening(true)
    r.onend = () => setListening(false)
    r.onresult = (e) => send(e.results[0][0].transcript)
    r.start()
  }

  const idx = STEPS[flow].indexOf(state?.step)

  return (
    <div className="grid gap-5 lg:grid-cols-[1.25fr_1fr]">
      <Panel title={t('conversation')} bodyClass=""
        subtitle={t('conversation_sub')}
        action={
          <div className="flex gap-1 rounded-lg bg-[#f1f3f8] p-0.5">
            {['loan', 'onboarding'].map((f) => (
              <button key={f} onClick={() => begin(f)}
                className={cx('rounded-md px-2.5 py-1 text-[12px] font-semibold',
                  flow === f ? 'bg-white text-[#14306b] shadow-sm' : 'text-[#77809a]')}>
                {t(f === 'loan' ? 'flow_loan' : 'flow_onboarding')}</button>
            ))}
          </div>
        }>
        <div className="flex h-[480px] flex-col">
          <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
            {msgs.map((m, i) => (
              <div key={i} className={cx('flex', m.who === 'me' ? 'justify-end' : 'justify-start')}>
                <div className={cx('max-w-[82%] rounded-xl px-3.5 py-2.5 text-[13px] leading-relaxed',
                  m.who === 'me' ? 'bg-[#14306b] text-white' : 'bg-[#f4f6fa] text-[#1b2333]')}>
                  <span lang={lang}>{m.text}</span>
                  {m.meta?.mandatory && <div className="mt-2"><Pill tone="blue">{m.meta.mandatory}</Pill></div>}
                  {m.meta?.halted && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {m.meta.offer?.map((o) => <Pill key={o} tone="amber">{o.replace(/_/g, ' ')}</Pill>)}
                    </div>
                  )}
                  {m.meta?.kfs && (
                    <div className="mt-2.5 rounded-lg border border-[#e6e8ef] bg-white p-3">
                      <p className="mb-1.5 text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[#8a93a8]">
                        Key Fact Statement
                      </p>
                      {m.meta.kfs.lines.map((l, k) => (
                        <p key={k} className="text-[12px] leading-relaxed text-[#4a5468]">{l}</p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {state?.choices?.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {state.choices.map((c) => (
                  <button key={c.id} onClick={() => send(c.id)} lang={lang}
                    className="rounded-full border border-[#dfe3ec] bg-white px-3 py-1.5 text-[12.5px] font-medium text-[#14306b] hover:border-[#14306b]/40">
                    {c.label}
                  </button>
                ))}
              </div>
            )}
            {state?.kind === 'consent' && (
              <div className="flex gap-1.5">
                {['yes', 'no'].map((v) => (
                  <button key={v} onClick={() => send(v)}
                    className="rounded-full border border-[#dfe3ec] bg-white px-4 py-1.5 text-[12.5px] font-semibold text-[#14306b] hover:border-[#14306b]/40">
                    {v}
                  </button>
                ))}
              </div>
            )}
            <div ref={endRef} />
          </div>
          <div className="flex items-center gap-2 border-t border-[#eef0f5] px-4 py-3">
            <button onClick={mic} title="Voice input"
              className={cx('grid h-8 w-8 shrink-0 place-items-center rounded-lg text-[14px]',
                listening ? 'animate-pulse bg-red-500 text-white' : 'bg-[#f1f3f8]')}>🎤</button>
            <input id="journey-input" value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send(input)} placeholder={t('type_reply')}
              className="min-w-0 flex-1 rounded-lg bg-[#f1f3f8] px-3 py-2 text-[13px] outline-none" />
            <button onClick={() => send(input)}
              className="shrink-0 rounded-lg bg-[#14306b] px-3.5 py-2 text-[12.5px] font-semibold text-white">{t('send')}</button>
          </div>
        </div>
      </Panel>

      <div className="space-y-5">
        <Panel title={t('regulated_script')}
          subtitle={t('regulated_sub')}>
          <ol className="space-y-0">
            {STEPS[flow].map((s, i) => (
              <li key={s} className={cx('flex items-center gap-3 rounded-lg px-2 py-2',
                i === idx && 'bg-[#14306b]/5')}>
                <span className={cx('grid h-6 w-6 shrink-0 place-items-center rounded-full text-[11px] font-semibold',
                  i < idx ? 'bg-emerald-500 text-white' : i === idx ? 'bg-[#14306b] text-white' : 'bg-[#eceef4] text-[#8a93a8]')}>
                  {i < idx ? '✓' : i + 1}
                </span>
                <span className={cx('flex-1 text-[13px] capitalize',
                  i === idx ? 'font-semibold text-[#14306b]' : 'text-[#4a5468]')}>
                  {s.replace(/_/g, ' ')}
                </span>
                {REGULATED.includes(s) && <Pill tone="blue">{t('required')}</Pill>}
              </li>
            ))}
          </ol>
        </Panel>

        {state?.halted && (
          <Panel title={t('journey_stopped')}>
            <p className="text-[13px] leading-relaxed text-[#4a5468]">
              The affordability check read a live stress score of <b className="tnum">{state.stress?.score}</b> and
              refused to continue the application.
            </p>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {state.stress?.fired.map((f) => <Pill key={f.code} tone="amber">{f.code}</Pill>)}
            </div>
            <p className="mt-3 text-[12px] text-[#77809a]">
              Recorded in the audit trail as loan_journey_stopped.
            </p>
          </Panel>
        )}

        <Panel title={t('captured')}>
          <pre className="overflow-x-auto text-[12px] leading-relaxed text-[#4a5468]">
{JSON.stringify(Object.fromEntries(Object.entries(state?.slots || {}).filter(([k]) => k !== 'kfs')), null, 2)}
          </pre>
        </Panel>
      </div>
    </div>
  )
}
