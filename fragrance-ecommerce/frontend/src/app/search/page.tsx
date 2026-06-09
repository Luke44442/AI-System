'use client'

import { useState, useEffect, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { productsApi } from '@/lib/api'
import ProductGrid from '@/components/product/ProductGrid'
import type { Product } from '@/types'

export default function SearchPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const inputRef = useRef<HTMLInputElement>(null)
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [products, setProducts] = useState<Product[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    const q = searchParams.get('q') || ''
    setQuery(q)
    if (q.trim().length >= 2) {
      fetchResults(q)
    } else {
      fetchFeatured()
    }
  }, [searchParams])

  const fetchResults = async (q: string) => {
    setLoading(true)
    try {
      const res = await productsApi.list({ search: q, page_size: 40 })
      setProducts(res.data.items || [])
      setTotal(res.data.total || 0)
    } catch {
      setProducts([])
    } finally {
      setLoading(false)
    }
  }

  const fetchFeatured = async () => {
    setLoading(true)
    try {
      const res = await productsApi.list({ is_featured: true, page_size: 20 })
      setProducts(res.data.items || [])
      setTotal(0)
    } catch {
      setProducts([])
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`)
    }
  }

  const currentQuery = searchParams.get('q') || ''

  return (
    <div className="min-h-screen bg-obsidian pt-24 pb-16">
      <div className="container-luxury">
        {/* Search input */}
        <div className="max-w-2xl mx-auto mb-12">
          <form onSubmit={handleSearch} className="relative">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search fragrances, brands, notes..."
              className="input-luxury w-full pl-12 pr-16 py-4 text-lg"
            />
            <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-obsidian-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <button type="submit" className="absolute right-3 top-1/2 -translate-y-1/2 btn-gold px-4 py-1.5 text-sm">
              Search
            </button>
          </form>
        </div>

        {/* Results header */}
        <div className="mb-8">
          {currentQuery ? (
            <div>
              <h1 className="text-2xl font-playfair text-cream">
                {loading ? 'Searching...' : `${total} result${total !== 1 ? 's' : ''} for "${currentQuery}"`}
              </h1>
              {!loading && total === 0 && (
                <p className="text-obsidian-300 mt-2">Try a different search term or browse our collections below.</p>
              )}
            </div>
          ) : (
            <h1 className="text-2xl font-playfair text-cream">Featured Fragrances</h1>
          )}
        </div>

        <ProductGrid products={products} loading={loading} />

        {/* Quick brand links */}
        {!currentQuery && (
          <div className="mt-16">
            <h2 className="text-xl font-playfair text-cream mb-6">Browse by Brand</h2>
            <div className="flex flex-wrap gap-3">
              {['Tom Ford', 'Dior', 'Creed', 'Chanel', 'YSL', 'MFK', 'Byredo', 'Le Labo', 'Versace', 'Prada'].map((brand) => (
                <a
                  key={brand}
                  href={`/search?q=${encodeURIComponent(brand)}`}
                  className="px-4 py-2 border border-obsidian-600 rounded-full text-sm text-obsidian-300 hover:border-gold-500 hover:text-gold-400 transition-colors"
                >
                  {brand}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
