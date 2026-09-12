import { AreaChart, Bar, Card, KeyValue, Panel, Pill, Stat, cx, inr } from '../components/ui'

export default function Overview({ view, timeline, t, onGo }) {
  const f = Object.fromEntries(view.features.map((x) => [x.key, x]))
  const stressed = view.stress.stressed
  const fraud = view.fraud.suspected
  const paused = view.held_back.filter((h) => h.suppressed_by === 'STRESS_PAUSE').length

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label={t('kpi_stress')} value={view.stress.score.toFixed(2)}
          tone={stressed ? 'bad' : view.stress.score > 0.3 ? 'warn' : 'good'}
          sub={stressed ? t('credit_paused_days', { n: view.stress.pause_days }) : t('below_threshold')} />
        <Stat label={t('kpi_fraud')} value={view.fraud.score.toFixed(2)}
          tone={fraud ? 'bad' : 'good'}
          sub={fraud ? t('hold_active') : t('normal_activity')} />
        <Stat label={t('kpi_income')} value={inr(f.monthly_income.value, true)}
          tone={f.inflow_30d_delta.value < -0.2 ? 'warn' : 'default'}
          sub={`${f.inflow_30d_delta.display} ${t('vs_last_month')}`} />
        <Stat label={t('kpi_withheld')} value={view.held_back.length}
          sub={paused ? t('n_paused_stress', { n: paused }) : t('none_paused')} />
      </div>

      {(stressed || fraud) && (
        <Card className={cx('border-l-4 px-5 py-4', fraud ? 'border-l-red-500' : 'border-l-amber-500')}>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="mb-1.5 flex items-center gap-2">
                <Pill tone={fraud ? 'red' : 'amber'}>{fraud ? t('protective_hold') : t('intervention_active')}</Pill>
                <span className="text-[12px] text-[#77809a]">{t('auto_logged')}</span>
              </div>
              <p className="text-[14px] font-semibold text-[#1b2333]">
                {fraud
                  ? t('transfers_held', { n: view.fraud.flagged_transactions.length })
                  : t('all_credit_paused', { n: view.stress.pause_days })}
              </p>
              <p className="mt-1 text-[12.5px] text-[#77809a]">
                {t('not_taken')}
              </p>
            </div>
            <button onClick={() => onGo('risk')}
              className="shrink-0 rounded-lg bg-[#14306b] px-3.5 py-2 text-[12.5px] font-semibold text-white hover:bg-[#1b3e87]">
              {t('review_signals')}
            </button>
          </div>
        </Card>
      )}

      <div className="grid gap-5 xl:grid-cols-[1.55fr_1fr]">
        <Panel title={t('money_in_out')} subtitle={t('twelve_months')}>
          <AreaChart data={timeline?.months || []} />
          <div className="mt-3 flex gap-5 border-t border-[#f0f2f7] pt-3">
            <span className="flex items-center gap-2 text-[12px] text-[#77809a]">
              <span className="h-0.5 w-5 rounded bg-[#14306b]" /> {t('money_in')}
            </span>
            <span className="flex items-center gap-2 text-[12px] text-[#77809a]">
              <span className="h-0.5 w-5 rounded border-t-2 border-dashed border-[#e08a1e]" /> {t('money_out')}
            </span>
          </div>
        </Panel>

        <Panel title={t('customer')} subtitle={view.segment}>
          <KeyValue rows={[
            { label: t('f_name'), value: view.customer.name },
            { label: t('f_occupation'), value: view.customer.occupation },
            { label: t('f_location'), value: `${view.customer.city}, ${view.customer.state}` },
            { label: t('f_language'), value: view.language_name },
            { label: t('f_emi'), value: f.emi_to_income.display,
              tone: f.emi_to_income.value > 0.5 ? 'text-amber-600' : '' },
            { label: t('f_savings'), value: f.savings_rate.display,
              tone: f.savings_rate.value < 0 ? 'text-red-600' : 'text-emerald-600' },
            { label: t('f_balance'), value: f.avg_balance_30d.display },
          ]} />
        </Panel>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel title={t('next_action')} subtitle={t('ranked_benefit')}
          action={<button onClick={() => onGo('recommendations')}
            className="text-[12px] font-semibold text-[#14306b] hover:underline">{t('view_all')}</button>}>
          {view.recommendations.length === 0 ? (
            <p className="py-6 text-center text-[13px] text-[#8a93a8]">
              {t('nothing_surfaced')} {view.personalisation_off ? t('consent_withdrawn') : t('no_product_cleared')}
            </p>
          ) : (
            <div className="space-y-3.5">
              {view.recommendations.slice(0, 2).map((r) => (
                <div key={r.product_id} className="rounded-lg bg-[#f8f9fc] px-4 py-3">
                  <div className="mb-1.5 flex items-center justify-between gap-3">
                    <span className="text-[13.5px] font-semibold text-[#14306b]">{r.name_en}</span>
                    <span className="tnum text-[12px] text-[#8a93a8]">
                      benefit {r.benefit.toFixed(2)} · propensity {r.propensity.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-[13px] leading-relaxed text-[#4a5468]">{r.reason_line}</p>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel title={t('portfolio_position')} subtitle={t('key_ratios')}
          action={<button onClick={() => onGo('portfolio')}
            className="text-[12px] font-semibold text-[#14306b] hover:underline">{t('open_portfolio')}</button>}>
          <div className="space-y-4">
            <Bar value={view.stress.score} label={t('kpi_stress')}
              tone={stressed ? 'red' : view.stress.score > 0.3 ? 'amber' : 'green'} />
            <Bar value={view.fraud.score} label={t('fraud_anomaly')} tone={fraud ? 'red' : 'green'} />
            <Bar value={Math.min(f.emi_to_income.value, 1)} label={t('emi_burden')}
              tone={f.emi_to_income.value > 0.5 ? 'amber' : 'blue'} />
            <Bar value={Math.max(0, Math.min(f.savings_rate.value, 1))} label={t('f_savings')} tone="green" />
          </div>
          <p className="mt-4 border-t border-[#f0f2f7] pt-3 text-[12px] leading-relaxed text-[#77809a]">
            {t('nightly_note')}
          </p>
        </Panel>
      </div>
    </div>
  )
}
