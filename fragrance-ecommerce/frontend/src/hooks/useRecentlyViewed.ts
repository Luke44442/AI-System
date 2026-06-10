'use client'

import { useCallback, useEffect, useState } from 'react'

const KEY = 'aurevia_recently_viewed'
const MAX = 12

function read(): string[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]')
  } catch {
    return []
  }
}

/** Tracks recently-viewed product IDs in localStorage (most-recent first). */
export function useRecentlyViewed() {
  const [ids, setIds] = useState<string[]>([])

  useEffect(() => { setIds(read()) }, [])

  const track = useCallback((productId: string) => {
    if (typeof window === 'undefined' || !productId) return
    const current = read().filter((id) => id !== productId)
    const next = [productId, ...current].slice(0, MAX)
    localStorage.setItem(KEY, JSON.stringify(next))
    setIds(next)
  }, [])

  return { ids, track }
}
