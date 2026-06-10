'use client'

import { useEffect, useState } from 'react'
import ProductCard from './ProductCard'
import type { Product } from '@/types'

interface RecommendationRowProps {
  title: string
  subtitle?: string
  /** Async loader returning the products for this row. */
  load: () => Promise<Product[]>
  /** Hide the whole section if the loader returns nothing. */
  hideWhenEmpty?: boolean
}

/** A titled horizontal-scrolling row of product cards, used for all
 *  recommendation surfaces (similar, complete the look, trending, recently viewed). */
export default function RecommendationRow({ title, subtitle, load, hideWhenEmpty = true }: RecommendationRowProps) {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    load()
      .then((p) => { if (active) setProducts(p || []) })
      .catch(() => { if (active) setProducts([]) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (loading) {
    return (
      <section className="py-8">
        <div className="h-5 w-48 bg-gray-200 rounded mb-6 animate-pulse" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="aspect-[3/4] bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </section>
    )
  }

  if (hideWhenEmpty && products.length === 0) return null

  return (
    <section className="py-8">
      <div className="mb-6">
        <h2 className="font-serif text-2xl text-obsidian">{title}</h2>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 lg:gap-6">
        {products.slice(0, 8).map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </section>
  )
}
