import { useEffect, useState } from 'react'
import { Panel, Pill, Stat, cx } from '../components/ui'
import { api } from '../api'

const GRADE = {
  critical: ['red', 'Critical'], high: ['amber', 'High'],
  watch: ['blue', 'Watch'], standard: ['green', 'Standard'],
}

const cr = (n) => (n >= 1000 ? `₹${(n / 1000).toFixed(2)}k cr` : `₹${Math.round(n).toLocaleString('en-IN')} cr`)

export default function Exposures() {
  const [data, setData] = useState(null)
  const [cases, setCases] = useState(null)
  const [grade, setGrade] = useState('all')
  const [openCase, setOpenCase] = useState(null)

  useEffect(() => {
    api.exposures().then(setData)
    api.exposureCases().then(setCases)
  }, [])

  if (!data || !cases) return null

  const rows = grade === 'all' ? data.rows : data.rows.filter((r) => r.grade === grade)
  const maxLag = Math.max(...cases.cases.map((c) => c.lag_months), 55)

  return (
    <div className="space-y-5">
      <Panel title="Why detection lag matters"
        subtitle={`${cases.premise.source}`}>
        <p className="max-w-[74ch] text-[14px] leading-relaxed text-[#1b2333]">
          {cases.premise.detail}
        </p>
        <a href={cases.premise.url} target="_blank" rel="noreferrer"
          className="mt-2 inline-block text-[12px] font-semibold text-[#14306b] hover:underline">
          Source →
        </a>
      </Panel>

      <Panel title={`Case files (${cases.cases.length})`}
        subtitle="Documented cases. Cited to show how long detection took, not to assert guilt.">
        <div className="space-y-2.5">
          {cases.cases.map((c) => {
            const open = openCase === c.id
            return (
              <div key={c.id} className={cx('rounded-lg border transition-colors',
                open ? 'border-[#14306b]/30 bg-[#fafbfd]' : 'border-[#e6e8ef] bg-white')}>
                <button onClick={() => setOpenCase(open ? null : c.id)}
                  className="flex w-full flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 text-left">
                  <span className="min-w-[200px] flex-1">
                    <span className="block text-[14px] font-semibold text-[#14306b]">{c.entity}</span>
                    <span className="block text-[12px] text-[#77809a]">
                      {c.people.join(', ')} · {c.sector}
                    </span>
                  </span>
                  <span className="tnum shrink-0 text-right">
                    <span className="block text-[13px] font-semibold text-[#1b2333]">{cr(c.amount_cr)}</span>
                    <span className="block text-[11.5px] text-[#8a93a8]">exposure</span>
                  </span>
                  <span className="tnum w-28 shrink-0 text-right">
                    <span className="block text-[13px] font-semibold text-red-600">{c.lag_months} months</span>
                    <span className="block text-[11.5px] text-[#8a93a8]">to detection</span>
                  </span>
                  <span className="shrink-0 text-[12px] font-semibold text-[#14306b]">
                    {open ? 'Close' : 'Open file'}
                  </span>
                </button>

                {open && (
                  <div className="border-t border-[#eef0f5] px-4 py-4">
                    <div className="mb-4 flex items-center gap-3">
                      <span className="w-24 shrink-0 text-[11.5px] text-[#8a93a8]">{c.first_signal}</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-[#eceef4]">
                        <div className="h-full rounded-full bg-red-400"
                          style={{ width: `${(c.lag_months / maxLag) * 100}%` }} />
                      </div>
                      <span className="w-28 shrink-0 text-right text-[11.5px] text-[#8a93a8]">{c.acted}</span>
                    </div>

                    <dl className="mb-4 grid gap-x-6 gap-y-2 sm:grid-cols-2">
                      {[['Named on record', c.people.join(', ')], ['Role', c.role],
                        ['Lender', c.banks], ['Signal visible', c.first_signal],
                        ['Action taken', c.acted]].map(([k, v]) => (
                        <div key={k} className="flex gap-3 text-[12.5px]">
                          <dt className="w-28 shrink-0 text-[#8a93a8]">{k}</dt>
                          <dd className="flex-1 text-[#1b2333]">{v}</dd>
                        </div>
                      ))}
                    </dl>

                    <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.07em] text-[#8a93a8]">
                      What was visible in the data
                    </p>
                    <p className="mb-3 max-w-[80ch] text-[13px] leading-relaxed text-[#4a5468]">{c.signal}</p>
                    <p className="mb-4 max-w-[80ch] text-[13px] leading-relaxed text-[#4a5468]">{c.detail}</p>

                    <div className="mb-4 rounded-lg bg-white p-3.5 ring-1 ring-[#e6e8ef]">
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.07em] text-[#8a93a8]">
                        Rules these documented facts would trigger
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {c.would_fire.map((code) => {
                          const rule = data.rules.find((r) => r.code === code)
                          return (
                            <span key={code} className="inline-flex items-center gap-2 rounded-md bg-amber-50 px-2.5 py-1">
                              <span className="text-[11px] font-semibold text-amber-700">{code}</span>
                              <span className="text-[11.5px] text-[#77809a]">{rule?.says}</span>
                            </span>
                          )
                        })}
                      </div>
                    </div>

                    {(() => {
                      const twin = data.rows.find((r) => r.modelled_on === c.id)
                      if (!twin) return null
                      return (
                        <div className="mb-4 rounded-lg border border-[#e6e8ef] bg-white px-3.5 py-3">
                          <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.07em] text-[#8a93a8]">
                            Equivalent in the monitored book
                          </p>
                          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                            <span className="text-[13.5px] font-semibold text-[#14306b]">{twin.entity}</span>
                            <span className="tnum text-[12.5px] text-[#4a5468]">{cr(twin.exposure_cr)}</span>
                            <span className="tnum text-[12.5px] font-semibold text-red-600">
                              risk {twin.risk_score.toFixed(2)}
                            </span>
                          </div>
                          <p className="mt-1.5 text-[12.5px] leading-relaxed text-[#77809a]">
                            An invented borrower carrying the same documented pattern — {twin.pattern.toLowerCase()}.
                            The engine flags it on day one, not {c.lag_months} months later.
                          </p>
                        </div>
                      )
                    })()}
                    <p className="mb-2 max-w-[80ch] text-[13px] leading-relaxed text-[#4a5468]">{c.outcome}</p>
                    <a href={c.url} target="_blank" rel="noreferrer"
                      className="text-[11.5px] font-semibold text-[#14306b] hover:underline">
                      {c.source} →
                    </a>
                  </div>
                )}
              </div>
            )
          })}
        </div>
        <p className="mt-4 rounded-lg bg-[#f8f9fc] px-4 py-3 text-[12px] leading-relaxed text-[#77809a]">
          {cases.retrospective_note} {cases.disclaimer}
        </p>
      </Panel>

      <Panel title="The same pattern at household scale"
        subtitle="ArthSaathi is a retail product. Each corporate red flag has an equivalent it watches daily." bodyClass="">
        <div className="overflow-x-auto">
          <table className="w-full text-[12.5px]">
            <thead>
              <tr className="border-b border-[#eef0f5] text-[11px] uppercase tracking-[0.07em] text-[#8a93a8]">
                <th className="px-5 py-2.5 text-left font-semibold">Corporate pattern</th>
                <th className="px-3 py-2.5 text-left font-semibold">Retail equivalent</th>
                <th className="px-5 py-2.5 text-left font-semibold">Signal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f4f5f9]">
              {cases.translation.map((t) => (
                <tr key={t.signal}>
                  <td className="px-5 py-2.5 text-[#4a5468]">{t.corporate}</td>
                  <td className="px-3 py-2.5 text-[#4a5468]">{t.retail}</td>
                  <td className="px-5 py-2.5"><code className="text-[11.5px] text-[#14306b]">{t.signal}</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label="Entities monitored" value={data.summary.entities} sub="Fictional book, for the prototype" />
        <Stat label="Total exposure" value={cr(data.summary.total_exposure_cr)} />
        <Stat label="Flagged" value={data.summary.flagged} tone="warn"
          sub={`${((data.summary.flagged / data.summary.entities) * 100).toFixed(0)}% of the book`} />
        <Stat label="Exposure at risk" value={cr(data.summary.flagged_exposure_cr)} tone="bad" />
      </div>

      <Panel title="Large exposure monitor"
        subtitle="Invented entities, scored by the same rule engine as retail using the corporate rule set."
        bodyClass=""
        action={
          <div className="flex gap-1 rounded-lg bg-[#f1f3f8] p-0.5">
            {['all', 'critical', 'high', 'watch'].map((g) => (
              <button key={g} onClick={() => setGrade(g)}
                className={cx('rounded-md px-2.5 py-1 text-[12px] font-semibold capitalize',
                  grade === g ? 'bg-white text-[#14306b] shadow-sm' : 'text-[#77809a]')}>{g}</button>
            ))}
          </div>
        }>
        <div className="max-h-[560px] overflow-auto">
          <table className="w-full text-[12.5px]">
            <thead className="sticky top-0 bg-white">
              <tr className="border-b border-[#eef0f5] text-[11px] uppercase tracking-[0.07em] text-[#8a93a8]">
                <th className="px-5 py-2.5 text-left font-semibold">Entity</th>
                <th className="px-3 py-2.5 text-left font-semibold">Sector</th>
                <th className="px-3 py-2.5 text-right font-semibold">Exposure</th>
                <th className="px-3 py-2.5 text-right font-semibold">Cover</th>
                <th className="px-3 py-2.5 text-right font-semibold">DSCR</th>
                <th className="px-3 py-2.5 text-right font-semibold">Risk</th>
                <th className="px-5 py-2.5 text-left font-semibold">Triggers</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f4f5f9]">
              {rows.map((r) => {
                const [tone, label] = GRADE[r.grade]
                return (
                  <tr key={r.exposure_id}>
                    <td className="whitespace-nowrap px-5 py-2.5 font-medium text-[#1b2333]"
                      title={r.pattern || undefined}>
                      {r.entity}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-[#77809a]">{r.sector}</td>
                    <td className="tnum whitespace-nowrap px-3 py-2.5 text-right text-[#4a5468]">{cr(r.exposure_cr)}</td>
                    <td className={cx('tnum px-3 py-2.5 text-right',
                      r.collateral_cover < 0.8 ? 'font-semibold text-red-600' : 'text-[#4a5468]')}>
                      {r.collateral_cover.toFixed(2)}
                    </td>
                    <td className={cx('tnum px-3 py-2.5 text-right',
                      r.dscr < 1 ? 'font-semibold text-red-600' : 'text-[#4a5468]')}>{r.dscr.toFixed(2)}</td>
                    <td className="px-3 py-2.5 text-right">
                      <span className="inline-flex items-center gap-2">
                        <span className="tnum font-semibold text-[#1b2333]">{r.risk_score.toFixed(2)}</span>
                        <Pill tone={tone}>{label}</Pill>
                      </span>
                    </td>
                    <td className="px-5 py-2.5">
                      <div className="flex flex-wrap gap-1">
                        {r.fired.slice(0, 3).map((f) => <Pill key={f.code} tone="amber">{f.code}</Pill>)}
                        {r.fired.length > 3 && <span className="text-[11px] text-[#9aa2b5]">+{r.fired.length - 3}</span>}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}
