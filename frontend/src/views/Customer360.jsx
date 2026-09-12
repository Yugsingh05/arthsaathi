import { Panel, Pill, cx, inr } from '../components/ui'

export default function Customer360({ view, txns, timeline, t }) {
  const top = timeline?.categories || []
  const max = Math.max(...top.map((c) => c.amount), 1)

  return (
    <div className="space-y-5">
      <div className="grid gap-5 lg:grid-cols-[1fr_1.35fr]">
        <Panel title={t('signals_read')}
          subtitle={t('point_in_time')}
          bodyClass="px-5 py-1">
          <div className="divide-y divide-[#f0f2f7]">
            {view.features.map((f) => (
              <div key={f.key} className="flex items-center justify-between gap-4 py-2.5">
                <span className="text-[12.5px] text-[#4a5468]">{f.label}</span>
                <span className="tnum text-[13px] font-semibold text-[#1b2333]">{f.display}</span>
              </div>
            ))}
          </div>
        </Panel>

        <div className="space-y-5">
          <Panel title={t('where_money_goes')} subtitle={t('debits_12m')}>
            <div className="space-y-2.5">
              {top.map((c) => (
                <div key={c.category}>
                  <div className="mb-1 flex items-baseline justify-between">
                    <span className="text-[12.5px] capitalize text-[#4a5468]">{c.category}</span>
                    <span className="tnum text-[12.5px] font-semibold text-[#1b2333]">{inr(c.amount, true)}</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-[#eceef4]">
                    <div className="h-full rounded-full bg-[#14306b]/70" style={{ width: `${(c.amount / max) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title={t('excluded')}
            subtitle={t('fairness_only')}>
            <div className="flex flex-wrap gap-1.5">
              {view.bias_guard?.dropped.map((d) => <Pill key={d}>{d}</Pill>)}
            </div>
          </Panel>
        </div>
      </div>

      <Panel title={t('transactions')} subtitle={t('parsed_from')} bodyClass="">
        <div className="overflow-x-auto">
          <table className="w-full text-[12.5px]">
            <thead>
              <tr className="border-b border-[#eef0f5] text-[11px] uppercase tracking-[0.07em] text-[#8a93a8]">
                <th className="px-5 py-2.5 text-left font-semibold">{t('th_date')}</th>
                <th className="px-3 py-2.5 text-left font-semibold">{t('th_counterparty')}</th>
                <th className="px-3 py-2.5 text-left font-semibold">{t('th_rail')}</th>
                <th className="px-3 py-2.5 text-left font-semibold">{t('th_category')}</th>
                <th className="px-3 py-2.5 text-right font-semibold">{t('th_amount')}</th>
                <th className="px-5 py-2.5 text-right font-semibold">{t('th_balance')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f4f5f9]">
              {txns.slice(0, 14).map((t) => (
                <tr key={t.txn_id} className={cx(t.hour < 5 && 'bg-red-50/50')}>
                  <td className="whitespace-nowrap px-5 py-2.5 text-[#77809a]">
                    {t.txn_date}
                    {t.hour < 5 && <span className="ml-1.5 text-[11px] font-semibold text-red-600">{t.hour}:00</span>}
                  </td>
                  <td className="max-w-[220px] truncate px-3 py-2.5 font-medium text-[#1b2333]">
                    {t.counterparty || '—'}
                  </td>
                  <td className="px-3 py-2.5"><Pill>{t.parsed_rail}</Pill></td>
                  <td className="px-3 py-2.5 capitalize text-[#77809a]">{t.parsed_category.replace(/_/g, ' ')}</td>
                  <td className={cx('tnum whitespace-nowrap px-3 py-2.5 text-right font-semibold',
                    t.direction === 'credit' ? 'text-emerald-600' : 'text-[#1b2333]')}>
                    {t.direction === 'credit' ? '+' : '−'}{inr(t.amount)}
                  </td>
                  <td className="tnum whitespace-nowrap px-5 py-2.5 text-right text-[#77809a]">{inr(t.balance_after)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}
