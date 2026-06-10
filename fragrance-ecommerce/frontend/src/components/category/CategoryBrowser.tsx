'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { productsApi, categoriesApi, brandsApi, type CategoryAttribute } from '@/lib/api'
import ProductGrid from '@/components/product/ProductGrid'
import type { Product, Brand } from '@/types'

interface CategoryBrowserProps {
  categorySlug: string
}

const SORT_OPTIONS = [
  { value: 'created_at:desc', label: 'Newest' },
  { value: 'website_price:asc', label: 'Price: Low to High' },
  { value: 'website_price:desc', label: 'Price: High to Low' },
  { value: 'order_count:desc', label: 'Best Selling' },
]

export default function CategoryBrowser({ categorySlug }: CategoryBrowserProps) {
  const [schema, setSchema] = useState<CategoryAttribute[]>([])
  const [brands, setBrands] = useState<Brand[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)

  // Filter state
  const [attrFilters, setAttrFilters] = useState<Record<string, string>>({})
  const [brandId, setBrandId] = useState<string>('')
  const [minPrice, setMinPrice] = useState<string>('')
  const [maxPrice, setMaxPrice] = useState<string>('')
  const [sort, setSort] = useState('created_at:desc')
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)

  // Load the category attribute schema + brand list once
  useEffect(() => {
    let active = true
    Promise.all([
      categoriesApi.getAttributes(categorySlug).catch(() => ({ attributes: [] as CategoryAttribute[] })),
      brandsApi.list().catch(() => [] as Brand[]),
    ]).then(([schemaRes, brandRes]) => {
      if (!active) return
      setSchema((schemaRes.attributes || []).filter((a) => a.is_filterable))
      setBrands(brandRes)
    })
    return () => { active = false }
  }, [categorySlug])

  const fetchProducts = useCallback(async () => {
    setLoading(true)
    try {
      const [sortBy, sortDir] = sort.split(':') as [string, 'asc' | 'desc']
      const activeAttrs = Object.fromEntries(Object.entries(attrFilters).filter(([, v]) => v))
      const res = await productsApi.list({
        category_slug: categorySlug,
        brand_id: brandId || undefined,
        min_price: minPrice ? Number(minPrice) : undefined,
        max_price: maxPrice ? Number(maxPrice) : undefined,
        attributes: Object.keys(activeAttrs).length ? JSON.stringify(activeAttrs) : undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
        page,
        page_size: 24,
      })
      setProducts(res.items || [])
      setTotal(res.total || 0)
    } catch {
      setProducts([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [categorySlug, brandId, minPrice, maxPrice, attrFilters, sort, page])

  useEffect(() => { fetchProducts() }, [fetchProducts])

  // Reset to page 1 whenever a filter changes
  useEffect(() => { setPage(1) }, [brandId, minPrice, maxPrice, attrFilters, sort])

  const setAttr = (key: string, value: string) =>
    setAttrFilters((prev) => ({ ...prev, [key]: prev[key] === value ? '' : value }))

  const clearAll = () => {
    setAttrFilters({}); setBrandId(''); setMinPrice(''); setMaxPrice(''); setSort('created_at:desc')
  }

  const activeFilterCount = useMemo(
    () => Object.values(attrFilters).filter(Boolean).length + (brandId ? 1 : 0) + (minPrice || maxPrice ? 1 : 0),
    [attrFilters, brandId, minPrice, maxPrice]
  )

  const totalPages = Math.max(1, Math.ceil(total / 24))

  const FilterPanel = (
    <div className="space-y-8">
      {activeFilterCount > 0 && (
        <button onClick={clearAll} className="text-xs text-gold-500 hover:text-gold-400 uppercase tracking-wider">
          Clear all ({activeFilterCount})
        </button>
      )}

      {/* Brand */}
      {brands.length > 0 && (
        <div>
          <h3 className="text-xs uppercase tracking-widest text-obsidian font-medium mb-3">Brand</h3>
          <select
            value={brandId}
            onChange={(e) => setBrandId(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white"
          >
            <option value="">All brands</option>
            {brands.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>
      )}

      {/* Price */}
      <div>
        <h3 className="text-xs uppercase tracking-widest text-obsidian font-medium mb-3">Price</h3>
        <div className="flex items-center gap-2">
          <input type="number" placeholder="Min" value={minPrice} onChange={(e) => setMinPrice(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <span className="text-gray-400">–</span>
          <input type="number" placeholder="Max" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        </div>
      </div>

      {/* Dynamic category attributes */}
      {schema.map((attr) => (
        <div key={attr.key}>
          <h3 className="text-xs uppercase tracking-widest text-obsidian font-medium mb-3">
            {attr.label}{attr.unit ? ` (${attr.unit})` : ''}
          </h3>
          {attr.data_type === 'enum' && attr.options.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {attr.options.map((opt) => (
                <button
                  key={opt}
                  onClick={() => setAttr(attr.key, opt)}
                  className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                    attrFilters[attr.key] === opt
                      ? 'bg-obsidian text-white border-obsidian'
                      : 'bg-white text-obsidian border-gray-300 hover:border-gold-500'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          ) : (
            <input
              type={attr.data_type === 'number' ? 'number' : 'text'}
              placeholder={`Filter by ${attr.label.toLowerCase()}`}
              value={attrFilters[attr.key] || ''}
              onChange={(e) => setAttrFilters((prev) => ({ ...prev, [attr.key]: e.target.value }))}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          )}
        </div>
      ))}
    </div>
  )

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-8">
      {/* Desktop filters */}
      <aside className="hidden lg:block">{FilterPanel}</aside>

      {/* Mobile filter toggle */}
      <div className="lg:hidden flex items-center justify-between">
        <button
          onClick={() => setMobileFiltersOpen((o) => !o)}
          className="btn-outline text-xs px-4 py-2"
        >
          Filters{activeFilterCount > 0 ? ` (${activeFilterCount})` : ''}
        </button>
      </div>
      {mobileFiltersOpen && (
        <div className="lg:hidden bg-white border border-gray-200 rounded-lg p-5">{FilterPanel}</div>
      )}

      {/* Results */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <p className="text-sm text-gray-500">{total} {total === 1 ? 'item' : 'items'}</p>
          <select value={sort} onChange={(e) => setSort(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2 text-sm bg-white">
            {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>

        <ProductGrid products={products} loading={loading} />

        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-3 mt-12">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
              className="btn-outline px-4 py-2 text-xs disabled:opacity-40">Previous</button>
            <span className="text-sm text-gray-500">Page {page} of {totalPages}</span>
            <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
              className="btn-outline px-4 py-2 text-xs disabled:opacity-40">Next</button>
          </div>
        )}
      </div>
    </div>
  )
}
