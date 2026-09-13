import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { cx } from './ui'

export default function CustomerSearch({ lang, onPick, t }) {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [hits, setHits] = useState([])
  const [hi, setHi] = useState(0)
  const box = useRef(null)

  useEffect(() => {
    const onDoc = (e) => {
      if (!box.current?.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  useEffect(() => {
    if (!open) return
    let cancelled = false
    const id = setTimeout(() => {
      api.customers(q, lang).then((rows) => {
        if (cancelled) return
        setHits(rows)
        setHi(0)
      }).catch(() => {})
    }, 160)
    return () => { cancelled = true; clearTimeout(id) }
  }, [q, open, lang])

  const pick = (c) => {
    onPick(c.customer_id, c)
    setQ('')
    setOpen(false)
  }

  const onKey = (e) => {
    if (e.key === 'Escape') { setOpen(false); return }
    if (!open || !hits.length) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHi((i) => Math.min(i + 1, hits.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHi((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && hits[hi]) {
      e.preventDefault()
      pick(hits[hi])
    }
  }

  return (
    <div ref={box} className="relative w-[min(100%,280px)]">
      <input
        id="customer-search"
        value={q}
        onChange={(e) => { setQ(e.target.value); setOpen(true) }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKey}
        placeholder={t('search_customer')}
        autoComplete="off"
        className="w-full rounded-lg border border-[#dfe3ec] bg-white px-2.5 py-1.5 text-[12.5px] font-medium outline-none placeholder:font-normal placeholder:text-[#9aa2b5]"
      />
      {open && (
        <div className="absolute right-0 z-30 mt-1 max-h-72 w-[min(100vw-2rem,360px)] overflow-auto rounded-xl border border-[#e6e8ef] bg-white py-1 shadow-lg">
          {hits.length === 0 ? (
            <p className="px-3 py-3 text-[12.5px] text-[#8a93a8]">{t('no_customers')}</p>
          ) : hits.map((c, i) => (
            <button
              key={c.customer_id}
              onMouseEnter={() => setHi(i)}
              onClick={() => pick(c)}
              className={cx(
                'flex w-full flex-col items-start px-3 py-2 text-left',
                i === hi ? 'bg-[#14306b]/8' : 'hover:bg-[#f6f7fb]',
              )}
            >
              <span className="text-[13px] font-semibold text-[#1b2333]">{c.name}</span>
              <span className="text-[11.5px] text-[#77809a]">
                {c.customer_id} · {c.city} · {c.occupation}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
