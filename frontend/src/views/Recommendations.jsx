import { useState } from 'react'
import { Panel, Pill, cx, pct } from '../components/ui'

const HELD_TONE = {
  STRESS_PAUSE: ['red', 'stopped_stress'],
  NOT_ELIGIBLE: ['slate', 'stopped_ineligible'],
  RANKED_BELOW: ['slate', 'stopped_ranked'],
  BELOW_BENEFIT_FLOOR: ['slate', 'stopped_floor'],
  FREQUENCY_CAP: ['amber', 'stopped_cap'],
}

export default function Recommendations({ view, onAct, acted, t }) {
  const [open, setOpen] = useState(view.recommendations[0]?.product_id ?? null)

  return (
    <div className="space-y-5">
      <Panel title={t('surfaced')}
        subtitle={t('ranked_benefit')}>
        {view.personalisation_off ? (
          <p className="py-8 text-center text-[13px] text-[#8a93a8]">
            {t('consent_withdrawn')}
          </p>
        ) : (
          <div className="space-y-3">
            {view.recommendations.map((r) => (
              <div key={r.product_id} className="rounded-lg border border-[#e6e8ef]">
                <div className="flex flex-wrap items-start justify-between gap-4 px-4 py-3.5">
                  <div className="min-w-[240px] flex-1">
                    <div className="mb-1.5 flex items-center gap-2">
                      <span className="text-[14px] font-semibold text-[#14306b]">{r.name}</span>
                      {r.is_credit && <Pill tone="amber">credit</Pill>}
                    </div>
                    <p className="text-[13px] leading-relaxed text-[#4a5468]">{r.reason_line_en}</p>
                    <p className="mt-2 rounded bg-[#f8f9fc] px-3 py-2 text-[13px] leading-relaxed text-[#1b2333]">
                      <span className="mr-2 text-[11px] font-semibold uppercase tracking-wide text-[#8a93a8]">
                        {view.language_name}
                      </span>
                      <span lang={view.language}>{r.reason_line} {r.benefit_line}</span>
                    </p>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-2">
                    <div className="tnum text-right text-[12px] text-[#77809a]">
                      <div>benefit <b className="text-[#1b2333]">{pct(r.benefit)}</b></div>
                      <div>propensity <b className="text-[#1b2333]">{pct(r.propensity)}</b></div>
                      <div>score <b className="text-[#1b2333]">{pct(r.score)}</b></div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => setOpen(open === r.product_id ? null : r.product_id)}
                        className="rounded-lg border border-[#dfe3ec] px-3 py-1.5 text-[12px] font-semibold text-[#14306b]">
                        {open === r.product_id ? t('hide') : t('explain')}
                      </button>
                      <button onClick={() => onAct(r.product_id, 'request_product')} disabled={!!acted[r.product_id]}
                        className={cx('rounded-lg px-3 py-1.5 text-[12px] font-semibold',
                          acted[r.product_id] ? 'bg-emerald-50 text-emerald-700' : 'bg-[#14306b] text-white hover:bg-[#1b3e87]')}>
                        {acted[r.product_id] ? `✓ ${t('queued')}` : t('queue_call')}
                      </button>
                    </div>
                  </div>
                </div>
                {open === r.product_id && (
                  <div className="border-t border-[#eef0f5] bg-[#fafbfd] px-4 py-3.5">
                    <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.07em] text-[#8a93a8]">
                      {t('contributions')}
                    </p>
                    <div className="space-y-1.5">
                      {r.reasons?.map((x, i) => (
                        <div key={x.feature} className="flex items-center gap-3">
                          <span className="flex w-52 shrink-0 items-center gap-2">
                            <span className="text-[12.5px] capitalize text-[#4a5468]">
                              {x.feature.replace(/_/g, ' ')}
                            </span>
                            {i === 0 && <Pill tone="blue">{t('quoted')}</Pill>}
                          </span>
                          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[#eceef4]">
                            <div className="h-full rounded-full bg-emerald-500"
                              style={{ width: `${Math.min(100, Math.abs(x.shap) * 55)}%` }} />
                          </div>
                          <span className="tnum w-20 shrink-0 text-right text-[12px] text-[#77809a]">
                            +{x.shap.toFixed(3)}
                          </span>
                        </div>
                      ))}
                    </div>
                    <p className="mt-3 text-[12px] leading-relaxed text-[#77809a]">
                      {t('positive_only')}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel title={t('withheld_n', { n: view.held_back.length })}
        subtitle={t('withheld_sub')} bodyClass="">
        <div className="overflow-x-auto">
          <table className="w-full text-[12.5px]">
            <thead>
              <tr className="border-b border-[#eef0f5] text-[11px] uppercase tracking-[0.07em] text-[#8a93a8]">
                <th className="px-5 py-2.5 text-left font-semibold">{t('th_product')}</th>
                <th className="px-3 py-2.5 text-left font-semibold">{t('th_stopped')}</th>
                <th className="px-3 py-2.5 text-left font-semibold">{t('th_reason')}</th>
                <th className="px-3 py-2.5 text-right font-semibold">{t('th_propensity')}</th>
                <th className="px-5 py-2.5 text-right font-semibold">{t('th_benefit')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f4f5f9]">
              {view.held_back.map((h) => {
                const [tone, key] = HELD_TONE[h.suppressed_by] || ['slate', null]
                const label = key ? t(key) : h.suppressed_by
                return (
                  <tr key={h.product_id}>
                    <td className="whitespace-nowrap px-5 py-2.5 font-medium text-[#4a5468]">{h.name}</td>
                    <td className="px-3 py-2.5"><Pill tone={tone}>{label}</Pill></td>
                    <td className="max-w-[420px] px-3 py-2.5 text-[#77809a]">{h.reason_held}</td>
                    <td className="tnum px-3 py-2.5 text-right text-[#1b2333]">{pct(h.propensity)}</td>
                    <td className="tnum px-5 py-2.5 text-right text-[#1b2333]">{pct(h.benefit)}</td>
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
