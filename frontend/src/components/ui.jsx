export const cx = (...a) => a.filter(Boolean).join(' ')

export const inr = (n, compact = false) => {
  const v = Number(n) || 0
  if (compact && Math.abs(v) >= 100000) return `₹${(v / 100000).toFixed(1)}L`
  if (compact && Math.abs(v) >= 1000) return `₹${(v / 1000).toFixed(0)}k`
  return `₹${Math.round(v).toLocaleString('en-IN')}`
}

export function Card({ className, children }) {
  return <div className={cx('rounded-xl border border-[#e6e8ef] bg-white', className)}>{children}</div>
}

export function Panel({ title, subtitle, action, children, className, bodyClass }) {
  return (
    <Card className={className}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-4 border-b border-[#eef0f5] px-5 py-3.5">
          <div>
            <h3 className="text-[13.5px] font-semibold text-[#1b2333]">{title}</h3>
            {subtitle && <p className="mt-0.5 text-[12px] leading-relaxed text-[#77809a]">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className={bodyClass ?? 'p-5'}>{children}</div>
    </Card>
  )
}

export function Stat({ label, value, sub, tone = 'default' }) {
  const tones = {
    default: 'text-[#14306b]', good: 'text-emerald-600',
    warn: 'text-amber-600', bad: 'text-red-600',
  }
  return (
    <Card className="px-5 py-4">
      <p className="text-[11px] font-semibold uppercase tracking-[0.09em] text-[#8a93a8]">{label}</p>
      <p className={cx('tnum mt-1.5 text-[26px] font-semibold leading-none', tones[tone])}>{value}</p>
      {sub && <p className="mt-1.5 text-[12px] text-[#77809a]">{sub}</p>}
    </Card>
  )
}

export function Pill({ tone = 'slate', children }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-600',
    blue: 'bg-[#14306b]/8 text-[#14306b]',
    amber: 'bg-amber-50 text-amber-700',
    red: 'bg-red-50 text-red-700',
    green: 'bg-emerald-50 text-emerald-700',
  }
  return (
    <span className={cx('inline-flex shrink-0 items-center rounded px-2 py-0.5 text-[11px] font-semibold', tones[tone])}>
      {children}
    </span>
  )
}

export function Bar({ value, tone = 'blue', showValue = true, label }) {
  const tones = { blue: 'bg-[#14306b]', amber: 'bg-amber-500', red: 'bg-red-500', green: 'bg-emerald-500' }
  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="mb-1.5 flex items-baseline justify-between">
          {label && <span className="text-[12px] text-[#77809a]">{label}</span>}
          {showValue && <span className="tnum text-[13px] font-semibold text-[#1b2333]">{value.toFixed(2)}</span>}
        </div>
      )}
      <div className="h-1.5 overflow-hidden rounded-full bg-[#eceef4]">
        <div className={cx('h-full rounded-full transition-[width] duration-500', tones[tone])}
          style={{ width: `${Math.min(100, Math.max(1.5, value * 100))}%` }} />
      </div>
    </div>
  )
}

export function KeyValue({ rows }) {
  return (
    <dl className="divide-y divide-[#f0f2f7]">
      {rows.map((r) => (
        <div key={r.label} className="flex items-center justify-between gap-4 py-2 first:pt-0 last:pb-0">
          <dt className="text-[12.5px] text-[#77809a]">{r.label}</dt>
          <dd className={cx('tnum text-[13px] font-semibold', r.tone || 'text-[#1b2333]')}>{r.value}</dd>
        </div>
      ))}
    </dl>
  )
}

export function AreaChart({ data, height = 150 }) {
  if (!data?.length) return null
  const w = 620, pad = { t: 12, r: 8, b: 22, l: 46 }
  const vals = data.flatMap((d) => [d.inflow, d.outflow])
  const max = Math.max(...vals, 1)
  const iw = w - pad.l - pad.r, ih = height - pad.t - pad.b
  const x = (i) => pad.l + (i / Math.max(data.length - 1, 1)) * iw
  const y = (v) => pad.t + ih - (v / max) * ih
  const path = (key) => data.map((d, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(d[key]).toFixed(1)}`).join(' ')
  const area = `${path('inflow')} L${x(data.length - 1)},${pad.t + ih} L${pad.l},${pad.t + ih} Z`
  const ticks = [0, max / 2, max]

  return (
    <svg viewBox={`0 0 ${w} ${height}`} className="w-full" style={{ maxWidth: '100%' }} role="img"
      aria-label="Monthly money in and out">
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={pad.l} x2={w - pad.r} y1={y(t)} y2={y(t)} stroke="#eceef4" strokeWidth="1" />
          <text x={pad.l - 7} y={y(t) + 3.5} textAnchor="end" fill="#9aa2b5" fontSize="9.5" className="tnum">
            {t >= 1000 ? `${Math.round(t / 1000)}k` : Math.round(t)}
          </text>
        </g>
      ))}
      <path d={area} fill="#14306b" opacity="0.07" />
      <path d={path('inflow')} fill="none" stroke="#14306b" strokeWidth="1.8" strokeLinejoin="round" />
      <path d={path('outflow')} fill="none" stroke="#e08a1e" strokeWidth="1.6" strokeDasharray="3 3" strokeLinejoin="round" />
      {data.map((d, i) => (
        i % Math.ceil(data.length / 6) === 0 || i === data.length - 1 ? (
          <text key={d.month} x={x(i)} y={height - 6}
            textAnchor={i === data.length - 1 ? 'end' : i === 0 ? 'start' : 'middle'}
            fill="#9aa2b5" fontSize="9.5">
            {d.month.slice(5)}/{d.month.slice(2, 4)}
          </text>
        ) : null
      ))}
      <circle cx={x(data.length - 1)} cy={y(data[data.length - 1].inflow)} r="3.2" fill="#14306b" />
    </svg>
  )
}

export function Empty({ children }) {
  return <p className="py-8 text-center text-[13px] text-[#8a93a8]">{children}</p>
}
