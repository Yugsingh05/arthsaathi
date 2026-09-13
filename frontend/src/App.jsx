import { useCallback, useEffect, useState } from 'react'
import Overview from './views/Overview'
import Customer360 from './views/Customer360'
import Recommendations from './views/Recommendations'
import RiskMonitoring from './views/RiskMonitoring'
import Journeys from './views/Journeys'
import Portfolio from './views/Portfolio'
import Exposures from './views/Exposures'
import AuditTrail from './views/AuditTrail'
import { cx } from './components/ui'
import CustomerSearch from './components/CustomerSearch'
import { makeT } from './i18n'
import { api } from './api'

const NAV = [
  ['overview', 'nav_overview'],
  ['customer', 'nav_customer'],
  ['recommendations', 'nav_recommendations'],
  ['risk', 'nav_risk'],
  ['journeys', 'nav_journeys'],
  ['portfolio', 'nav_portfolio'],
  ['exposures', 'nav_exposures'],
  ['audit', 'nav_audit'],
]

const q = new URLSearchParams(window.location.search)
const LEGACY = { app: 'overview', assistant: 'journeys', ledger: 'audit', console: 'portfolio' }

function initialTab() {
  const t = q.get('tab')
  if (!t) return 'overview'
  if (NAV.some(([k]) => k === t)) return t
  return LEGACY[t] || 'overview'
}

export default function App() {
  const [meta, setMeta] = useState(null)
  const [tab, setTab] = useState(initialTab)
  const [cid, setCid] = useState(q.get('c') || 'CUST0001')
  const [asOf, setAsOf] = useState(q.get('t'))
  const [lang, setLang] = useState(q.get('lang') || 'gu')
  const [langPinned, setLangPinned] = useState(Boolean(q.get('lang')))
  const [view, setView] = useState(null)
  const [txns, setTxns] = useState([])
  const [timeline, setTimeline] = useState(null)
  const [acted, setActed] = useState({})
  const [err, setErr] = useState(null)
  const t = makeT(lang)

  useEffect(() => {
    api.meta(lang).then((m) => { setMeta(m); setAsOf((a) => a || m.checkpoints[0].date) })
      .catch((e) => setErr(String(e)))
  }, [lang])

  const reload = useCallback(() => {
    if (!asOf) return
    api.customer(cid, asOf, lang).then(setView).catch((e) => setErr(String(e)))
    api.transactions(cid, asOf, lang).then(setTxns).catch(() => {})
    api.timeline(cid, asOf, lang).then(setTimeline).catch(() => {})
  }, [cid, asOf, lang])

  useEffect(() => { reload(); setActed({}) }, [reload])




  
  useEffect(() => {
    if (!asOf) return
    const u = new URL(window.location.href)
    u.search = new URLSearchParams({ c: cid, t: asOf, lang, tab }).toString()
    window.history.replaceState(null, '', u)
  }, [cid, asOf, lang, tab])

  const pickCustomer = (id, customer) => {
    setCid(id)
    if (langPinned) return
    const langCode = customer?.language
      || meta?.demo_customers.find((x) => x.customer_id === id)?.language
    if (langCode) setLang(langCode)
  }

  const pickLang = (code) => {
    setLang(code)
    setLangPinned(true)
  }

  const act = async (key, action) => {
    setActed((a) => ({ ...a, [key]: action }))
    try { await api.intervention(cid, action, asOf) } catch { /* surfaced by the audit trail */ }
  }

  if (err) return (
    <div className="grid h-full place-items-center p-8 text-center">
      <div>
        <p className="text-[14px] font-semibold text-red-600">Cannot reach the API.</p>
        <p className="mt-1.5 text-[13px] text-[#77809a]">
          Start it with <code className="rounded bg-[#eceef4] px-1.5 py-0.5">uv run uvicorn app.main:app --port 8000</code>
        </p>
      </div>
    </div>
  )
  if (!meta || !view) return (
    <div className="grid h-full place-items-center text-[13px] text-[#8a93a8]">Loading…</div>
  )

  return (
    <div className="flex min-h-full">
      <aside className="hidden w-[228px] shrink-0 flex-col bg-[#0c1730] lg:flex">
        <div className="px-6 py-6">
          <p className="text-[17px] font-semibold tracking-tight text-white">ArthSaathi</p>
          <p className="mt-0.5 text-[11px] tracking-wide text-white/40">{t('tagline')}</p>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 px-3">
          {NAV.map(([k, label]) => (
            <button key={k} onClick={() => setTab(k)}
              className={cx('rounded-lg px-3 py-2 text-left text-[13px] font-medium transition-colors',
                tab === k ? 'bg-white/12 text-white' : 'text-white/55 hover:bg-white/6 hover:text-white/85')}>
              {t(label)}
            </button>
          ))}
        </nav>
        <div className="px-6 py-5">
          <p className="text-[11px] leading-relaxed text-white/30">
            {t('footnote')}
          </p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 border-b border-[#e6e8ef] bg-white/92 backdrop-blur">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 px-5 py-3 lg:px-7">
            <div className="min-w-0">
              <h1 className="truncate text-[16px] font-semibold tracking-tight text-[#1b2333]">
                {t(NAV.find(([k]) => k === tab)?.[1])}
              </h1>
              <p className="truncate text-[12px] text-[#77809a]">
                {view.customer.name} · {view.customer.occupation} · {t('as_of')} {asOf}
              </p>
            </div>

            <div className="ml-auto flex flex-wrap items-center gap-2">
              <CustomerSearch lang={lang} t={t} onPick={pickCustomer} />
              <span title="All customers and figures in this prototype are generated. No real customer data is used."
                className="hidden rounded-md bg-[#f1f3f8] px-2 py-1 text-[11px] font-semibold text-[#77809a] sm:inline">
                {t('synthetic')}
              </span>
              <div className="flex gap-0.5 rounded-lg bg-[#f1f3f8] p-0.5">
                {meta.languages.map((l) => (
                  <button key={l.code} onClick={() => pickLang(l.code)}
                    className={cx('rounded-md px-2 py-1 text-[12px] font-semibold',
                      lang === l.code ? 'bg-white text-[#14306b] shadow-sm' : 'text-[#77809a]')}>
                    {l.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

        </header>

        <main className="flex-1 px-5 py-5 lg:px-7 lg:py-6">
          {tab === 'overview' && <Overview view={view} timeline={timeline} t={t} onGo={setTab} />}
          {tab === 'customer' && <Customer360 view={view} txns={txns} timeline={timeline} t={t} />}
          {tab === 'recommendations' && <Recommendations view={view} onAct={act} acted={acted} t={t} />}
          {tab === 'risk' && <RiskMonitoring view={view} onAct={act} acted={acted} t={t} />}
          {tab === 'journeys' && <Journeys customerId={cid} lang={lang} asOf={asOf} t={t} />}
          {tab === 'portfolio' && <Portfolio asOf={asOf} cid={cid} lang={lang} t={t}
            onOpenCustomer={(id) => { pickCustomer(id); setTab('overview') }} />}
          {tab === 'exposures' && <Exposures />}
          {tab === 'audit' && <AuditTrail customerId={cid} view={view} onConsentChange={reload} t={t} />}
        </main>
      </div>
    </div>
  )
}
