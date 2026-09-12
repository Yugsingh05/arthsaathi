import { useEffect, useState } from 'react'
import { Panel, Pill, Stat, cx } from '../components/ui'
import { api } from '../api'

const KIND = {
  recommendation: ['slate', 'Recommendation'],
  stress_flag: ['amber', 'Stress flag'],
  fraud_flag: ['red', 'Fraud flag'],
  consent_change: ['blue', 'Consent change'],
  loan_journey_stopped: ['amber', 'Journey stopped'],
  loan_kfs_shown: ['blue', 'Key Fact Statement'],
}

export default function AuditTrail({ customerId, view, onConsentChange, t }) {
  const [data, setData] = useState(null)
  const [filter, setFilter] = useState('all')

  const load = () => api.ledger(customerId).then(setData)
  useEffect(() => { load() }, [customerId, view])

  const toggle = async (purpose, granted) => {
    await api.setConsent(customerId, purpose, granted)
    await load(); onConsentChange()
  }

  if (!data) return null

  const entries = data.entries.filter((e) =>
    filter === 'all' ? true : filter === 'withheld' ? e.shown === false : e.kind.includes(filter))

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label={t('offers_surfaced')} value={data.counts.offers_shown} />
        <Stat label={t('offers_withheld')} value={data.counts.offers_held_back}
          sub={t('regulator_asks')} />
        <Stat label={t('entries_for')} value={data.entries.length} />
      </div>

      <Panel title={t('consent')} subtitle={t('consent_sub')}>
        <div className="grid gap-3 sm:grid-cols-3">
          {Object.entries(view.purposes).map(([k, label]) => {
            const on = data.consents[k]
            return (
              <div key={k} className={cx('rounded-lg border px-4 py-3',
                on ? 'border-[#e6e8ef] bg-white' : 'border-amber-200 bg-amber-50/50')}>
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span className="text-[13px] font-semibold capitalize text-[#1b2333]">{k.replace(/_/g, ' ')}</span>
                  <button onClick={() => toggle(k, !on)} aria-label={`toggle ${k}`}
                    className={cx('relative h-5 w-9 shrink-0 rounded-full transition-colors',
                      on ? 'bg-emerald-500' : 'bg-[#cdd3e0]')}>
                    <span className={cx('absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all',
                      on ? 'left-[18px]' : 'left-0.5')} />
                  </button>
                </div>
                <p className="text-[12px] leading-relaxed text-[#77809a]">{label}</p>
              </div>
            )
          })}
        </div>
      </Panel>

      <Panel title={t('decision_log')} subtitle={t('same_rows')} bodyClass=""
        action={
          <div className="flex gap-1 rounded-lg bg-[#f1f3f8] p-0.5">
            {[['all', 'filter_all'], ['withheld', 'filter_withheld'], ['flag', 'filter_flags'], ['consent', 'filter_consent']].map(([k, l]) => (
              <button key={k} onClick={() => setFilter(k)}
                className={cx('rounded-md px-2.5 py-1 text-[12px] font-semibold',
                  filter === k ? 'bg-white text-[#14306b] shadow-sm' : 'text-[#77809a]')}>{t(l)}</button>
            ))}
          </div>
        }>
        <div className="max-h-[520px] divide-y divide-[#f4f5f9] overflow-y-auto">
          {entries.length === 0 && <p className="py-8 text-center text-[13px] text-[#8a93a8]">{t('no_entries')}</p>}
          {entries.map((e) => {
            const [tone, label] = KIND[e.kind] || ['slate', e.kind.replace(/[:_]/g, ' ')]
            return (
              <div key={e.entry_id} className="px-5 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Pill tone={tone}>{label}</Pill>
                  {e.product_id && <span className="text-[12.5px] font-semibold text-[#1b2333]">{e.product_id}</span>}
                  {e.shown === false && <Pill tone="red">{t('withheld_word')}</Pill>}
                  {e.shown === true && <Pill tone="green">{t('shown_word')}</Pill>}
                  <span className="tnum ml-auto text-[11.5px] text-[#9aa2b5]">{e.ts}</span>
                </div>
                {e.detail && <p className="mt-1.5 text-[12.5px] leading-relaxed text-[#4a5468]">{e.detail}</p>}
                <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-[11.5px] text-[#9aa2b5]">
                  <span>{t('purpose_word')}: {e.purpose}</span>
                  {e.features_used?.length > 0 && <span>{t('data_used')}: {e.features_used.join(', ')}</span>}
                  {e.reason_codes?.length > 0 && <span>{t('codes_word')}: {e.reason_codes.join(', ')}</span>}
                </div>
              </div>
            )
          })}
        </div>
      </Panel>
    </div>
  )
}
