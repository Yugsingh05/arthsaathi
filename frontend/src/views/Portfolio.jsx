import { useEffect, useState } from 'react'
import { Panel, Pill, Stat, cx, pct } from '../components/ui'
import { api } from '../api'

export default function Portfolio({ asOf, cid, lang, t, onOpenCustomer }) {
  const [queue, setQueue] = useState([])
  const [fair, setFair] = useState(null)
  const [note, setNote] = useState('')
  const [saved, setSaved] = useState(null)

  useEffect(() => {
    api.queue(asOf, lang).then(setQueue)
    api.fairness(asOf).then(setFair)
  }, [asOf, lang])

  const decide = async (d) => {
    await api.override(cid, d, note)
    setSaved(d); setNote('')
    setTimeout(() => setSaved(null), 2500)
  }

  const flagged = queue.filter((q) => q.stressed).length

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label={t('in_queue')} value={queue.length} />
        <Stat label={t('above_threshold')} value={flagged} tone={flagged ? 'warn' : 'good'} />
        <Stat label={t('models_prod')} value={Object.keys(fair?.model_auc || {}).length} />
      </div>

      <Panel title={t('review_queue')} subtitle={t('ranked_stress')} bodyClass="">
        <div className="overflow-x-auto">
          <table className="w-full text-[12.5px]">
            <thead>
              <tr className="border-b border-[#eef0f5] text-[11px] uppercase tracking-[0.07em] text-[#8a93a8]">
                <th className="px-5 py-2.5 text-left font-semibold">{t('customer')}</th>
                <th className="px-3 py-2.5 text-left font-semibold">{t('f_occupation')}</th>
                <th className="px-3 py-2.5 text-right font-semibold">{t('th_income')}</th>
                <th className="px-3 py-2.5 text-right font-semibold">{t('th_stress')}</th>
                <th className="px-3 py-2.5 text-left font-semibold">{t('th_triggers')}</th>
                <th className="px-5 py-2.5"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f4f5f9]">
              {queue.map((q) => (
                <tr key={q.customer_id} className={cx(q.customer_id === cid && 'bg-[#14306b]/4')}>
                  <td className="whitespace-nowrap px-5 py-2.5">
                    <span className="font-semibold text-[#1b2333]">{q.name}</span>
                    <span className="ml-2 text-[11.5px] text-[#8a93a8]">{q.city}</span>
                  </td>
                  <td className="whitespace-nowrap px-3 py-2.5 text-[#77809a]">{q.occupation}</td>
                  <td className="tnum whitespace-nowrap px-3 py-2.5 text-right text-[#4a5468]">{q.monthly_income}</td>
                  <td className={cx('tnum px-3 py-2.5 text-right font-semibold',
                    q.stress_score > 0.75 ? 'text-red-600' : q.stressed ? 'text-amber-600' : 'text-[#8a93a8]')}>
                    {pct(q.stress_score)}
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex flex-wrap gap-1">
                      {q.codes.slice(0, 3).map((c) => <Pill key={c} tone="amber">{c}</Pill>)}
                    </div>
                  </td>
                  <td className="px-5 py-2.5 text-right">
                    <button onClick={() => onOpenCustomer(q.customer_id)}
                      className="whitespace-nowrap text-[12px] font-semibold text-[#14306b] hover:underline">{t('open_word')}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="grid gap-5 lg:grid-cols-[1fr_1.3fr]">
        <Panel title={t('officer_decision')} subtitle={t('recorded_against')}>
          <input id="officer-note" value={note} onChange={(e) => setNote(e.target.value)}
            placeholder={t('note_placeholder')}
            className="mb-3 w-full rounded-lg bg-[#f1f3f8] px-3 py-2 text-[13px] outline-none" />
          <div className="flex flex-wrap items-center gap-2">
            <button onClick={() => decide('uphold')}
              className="rounded-lg bg-[#14306b] px-3.5 py-2 text-[12.5px] font-semibold text-white hover:bg-[#1b3e87]">
              {t('uphold')}
            </button>
            <button onClick={() => decide('override')}
              className="rounded-lg border border-[#dfe3ec] px-3.5 py-2 text-[12.5px] font-semibold text-[#14306b]">
              {t('override')}
            </button>
            {saved && <Pill tone="green">{t('recorded_as', { d: saved })}</Pill>}
          </div>
        </Panel>

        {fair && (
          <Panel title={t('fairness')} subtitle={fair.note} bodyClass="">
            <div className="grid divide-y divide-[#f0f2f7] sm:grid-cols-2 sm:divide-x sm:divide-y-0">
              {Object.entries(fair.panels).slice(0, 2).map(([attr, rows]) => (
                <div key={attr} className="px-5 py-4">
                  <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.07em] text-[#8a93a8]">{attr}</p>
                  <table className="w-full text-[12px]">
                    <thead>
                      <tr className="text-[#9aa2b5]">
                        <th className="pb-1 text-left font-medium">group</th>
                        <th className="pb-1 text-right font-medium">n</th>
                        <th className="pb-1 text-right font-medium">stress</th>
                        <th className="pb-1 text-right font-medium">benefit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.slice(0, 6).map((r) => (
                        <tr key={r.group} className="border-t border-[#f4f5f9]">
                          <td className="py-1 text-[#4a5468]">{r.group}</td>
                          <td className="tnum py-1 text-right text-[#8a93a8]">{r.n}</td>
                          <td className="tnum py-1 text-right text-[#1b2333]">{pct(r.stress_rate)}</td>
                          <td className="tnum py-1 text-right text-[#1b2333]">{pct(r.benefit_offer_rate)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          </Panel>
        )}
      </div>
    </div>
  )
}
