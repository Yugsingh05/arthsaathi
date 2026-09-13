import { Bar, Panel, Pill, cx, inr, pct } from '../components/ui'

const ACTIONS = [
  ['emi_holiday', 'act_defer', 'act_defer_sub'],
  ['restructure', 'act_extend', 'act_extend_sub'],
  ['call_back', 'act_call', 'act_call_sub'],
]

export default function RiskMonitoring({ view, onAct, acted, t }) {
  const stressed = view.stress.stressed
  const fraud = view.fraud.suspected

  return (
    <div className="space-y-5">
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel title={t('kpi_stress')}
          subtitle={t('risk_stress_sub', { t: pct(view.stress.threshold) })}>
          <Bar value={view.stress.score} label={t('composite')}
            tone={stressed ? 'red' : view.stress.score > 0.3 ? 'amber' : 'green'} />
          <div className="mt-3 flex gap-6 text-[12px] text-[#77809a]">
            <span>{t('rules_word')} <b className="tnum text-[#1b2333]">{pct(view.stress.rule_score)}</b></span>
            <span>{t('anomaly_word')} <b className="tnum text-[#1b2333]">{pct(view.stress.anomaly)}</b></span>
          </div>
          <div className="mt-4 space-y-2 border-t border-[#f0f2f7] pt-4">
            {view.stress.fired.length === 0 ? (
              <p className="text-[13px] text-[#8a93a8]">{t('no_rule_fired')}</p>
            ) : view.stress.fired.map((r) => (
              <div key={r.code} className="flex items-start gap-3">
                <Pill tone="amber">{r.code}</Pill>
                <span className="text-[12.5px] leading-snug text-[#4a5468]">{r.says}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title={t('fraud_anomaly')}
          subtitle={t('risk_fraud_sub', { t: pct(view.fraud.threshold) })}>
          <Bar value={view.fraud.score} label={t('composite')} tone={fraud ? 'red' : 'green'} />
          <div className="mt-4 space-y-2 border-t border-[#f0f2f7] pt-4">
            {view.fraud.fired.length === 0 ? (
              <p className="text-[13px] text-[#8a93a8]">{t('nothing_unusual')}</p>
            ) : view.fraud.fired.map((r) => (
              <div key={r.code} className="flex items-start gap-3">
                <Pill tone="red">{r.code}</Pill>
                <span className="text-[12.5px] leading-snug text-[#4a5468]">{r.says}</span>
              </div>
            ))}
          </div>
          {view.fraud.flagged_transactions?.length > 0 && (
            <div className="mt-4 border-t border-[#f0f2f7] pt-3">
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.07em] text-[#8a93a8]">{t('held_transfers')}</p>
              <div className="space-y-1.5">
                {view.fraud.flagged_transactions.slice(0, 5).map((t) => (
                  <div key={t.txn_id} className="flex items-center justify-between gap-3 text-[12.5px]">
                    <span className="truncate text-[#4a5468]">
                      {t.counterparty} <span className="text-[#8a93a8]">· {t.hour}:00</span>
                    </span>
                    <span className="tnum shrink-0 font-semibold text-[#1b2333]">{inr(t.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Panel>
      </div>

      <Panel title={t('interventions')}
        subtitle={t('interventions_sub')}>
        <div className="grid gap-3 sm:grid-cols-3">
          {ACTIONS.map(([id, label, sub]) => (
            <button key={id} onClick={() => onAct('help', id)} disabled={!!acted.help}
              className={cx('rounded-lg border px-4 py-3 text-left transition-colors',
                acted.help === id ? 'border-emerald-300 bg-emerald-50'
                  : acted.help ? 'border-[#e6e8ef] bg-white opacity-50'
                    : 'border-[#e6e8ef] bg-white hover:border-[#14306b]/40')}>
              <span className="block text-[13px] font-semibold text-[#1b2333]">
                {acted.help === id ? `✓ ${t(label)}` : t(label)}
              </span>
              <span className="mt-0.5 block text-[12px] text-[#77809a]">{t(sub)}</span>
            </button>
          ))}
        </div>
        {fraud && (
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {[['confirm_fraud', 'act_confirm_fraud', 'act_confirm_fraud_sub'],
              ['release_hold', 'act_release', 'act_release_sub']].map(([id, label, sub]) => (
              <button key={id} onClick={() => onAct('fraud', id)} disabled={!!acted.fraud}
                className={cx('rounded-lg border px-4 py-3 text-left transition-colors',
                  acted.fraud === id ? 'border-emerald-300 bg-emerald-50'
                    : acted.fraud ? 'border-[#e6e8ef] opacity-50' : 'border-red-200 bg-red-50/50 hover:border-red-300')}>
                <span className="block text-[13px] font-semibold text-[#1b2333]">
                  {acted.fraud === id ? `✓ ${t(label)}` : t(label)}
                </span>
                <span className="mt-0.5 block text-[12px] text-[#77809a]">{t(sub)}</span>
              </button>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}
