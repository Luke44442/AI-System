'use client'

import { useState } from 'react'
import { assistantApi } from '@/lib/api'
import ProductGrid from '@/components/product/ProductGrid'
import type { Product } from '@/types'

const SUGGESTIONS = [
  "I'm looking for a summer fragrance under $150",
  'Find me sneakers for a streetwear fit',
  'An outfit for a car meet',
  'Luxury gifts under $200',
]

export default function AssistantPage() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [searched, setSearched] = useState(false)

  const run = async (q: string) => {
    const text = q.trim()
    if (!text) return
    setQuery(text)
    setLoading(true)
    setSearched(true)
    try {
      const res = await assistantApi.recommend(text, 12)
      setMessage(res.message)
      setProducts(res.items || [])
    } catch {
      setMessage("I had trouble with that one — try rephrasing your request.")
      setProducts([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-cream pt-24 pb-16">
      <div className="container-luxury max-w-4xl">
        <div className="text-center mb-10">
          <p className="section-subtitle text-gold-600 mb-3">AI Concierge</p>
          <h1 className="section-title">What are you looking for?</h1>
          <p className="text-gray-500 mt-4 max-w-xl mx-auto">
            Describe a vibe, an occasion, or a budget — your Aurevia stylist will curate it.
          </p>
        </div>

        <form
          onSubmit={(e) => { e.preventDefault(); run(query) }}
          className="flex gap-2 max-w-2xl mx-auto mb-6"
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. an evening fragrance that lasts all night"
            className="flex-1 border border-gray-300 rounded-full px-5 py-3 text-sm focus:outline-none focus:border-gold-500"
          />
          <button type="submit" disabled={loading} className="btn-gold px-6 disabled:opacity-60">
            {loading ? '…' : 'Ask'}
          </button>
        </form>

        {!searched && (
          <div className="flex flex-wrap justify-center gap-2 mb-12">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => run(s)}
                className="px-4 py-2 text-xs rounded-full border border-gray-300 bg-white hover:border-gold-500 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {message && (
          <div className="bg-white border border-gray-200 rounded-2xl p-5 mb-8 max-w-2xl mx-auto">
            <p className="text-obsidian leading-relaxed">
              <span className="text-gold-600 font-serif text-lg mr-2">✦</span>
              {message}
            </p>
          </div>
        )}

        {searched && <ProductGrid products={products} loading={loading} />}
      </div>
    </div>
  )
}
