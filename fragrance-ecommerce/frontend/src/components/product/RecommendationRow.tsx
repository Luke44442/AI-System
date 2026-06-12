'use client'

import { useEffect, useState } from 'react'
import ProductCard from './ProductCard'
import { recommendationsApi } from '@/lib/api'
import type { Product } from '@/types'

/** Declarative source — serializable, so server components can render this row. */
export interface RecommendationSource {
  kind: 'trending' | 'bestsellers' | 'similar' | 'frequently-bought-together' | 'complete-the-look'
  productId?: string
  limit?: number
  categorySlug?: string
}

interface RecommendationRowProps {
  title: string
  subtitle?: string
  /** Async loader returning the products for this row (client trees only). */
  load?: () => Promise<Product[]>
  /** Serializable alternative to `load` — required when rendered from a server component. */
  source?: RecommendationSource
  /** Hide the whole section if the loader returns nothing. */
  hideWhenEmpty?: boolean
}

function loadFromSource(source: RecommendationSource): Promise<Product[]> {
  const limit = source.limit ?? 8
  switch (source.kind) {
    case 'trending':
      return recommendationsApi.trending(limit, source.categorySlug)
    case 'bestsellers':
      return recommendationsApi.bestsellers(limit, source.categorySlug)
    case 'similar':
      return source.productId ? recommendationsApi.similar(source.productId, limit) : Promise.resolve([])
    case 'frequently-bought-together':
      return source.productId ? recommendationsApi.frequentlyBoughtTogether(source.productId, limit) : Promise.resolve([])
    case 'complete-the-look':
      return source.productId ? recommendationsApi.completeTheLook(source.productId, limit) : Promise.resolve([])
    default:
      return Promise.resolve([])
  }
}

/** A titled horizontal-scrolling row of product cards, used for all
 *  recommendation surfaces (similar, complete the look, trending, recently viewed). */
export default function RecommendationRow({ title, subtitle, load, source, hideWhenEmpty = true }: RecommendationRowProps) {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    const loader = load ?? (source ? () => loadFromSource(source) : () => Promise.resolve([]))
    loader()
      .then((p) => { if (active) setProducts(p || []) })
      .catch(() => { if (active) setProducts([]) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (loading) {
    return (
      <section className="py-8">
        <div className="h-5 w-48 skeleton rounded mb-6" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="aspect-[3/4] skeleton rounded" />
          ))}
        </div>
      </section>
    )
  }

  if (hideWhenEmpty && products.length === 0) return null

  return (
    <section className="py-8">
      <div className="mb-6">
        <h2 className="font-serif text-2xl text-cream">{title}</h2>
        {subtitle && <p className="text-sm text-white/40 mt-1">{subtitle}</p>}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 lg:gap-6">
        {products.slice(0, 8).map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </section>
  )
}
