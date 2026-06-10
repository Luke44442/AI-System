import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import ProductGrid from '@/components/product/ProductGrid'

async function getBrandData(slug: string) {
  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
  try {
    const [brandsRes, productsRes] = await Promise.all([
      fetch(`${API}/brands`, { next: { revalidate: 3600 } }),
      fetch(`${API}/products?brand_slug=${slug}&page_size=60&is_active=true`, { next: { revalidate: 1800 } }),
    ])
    const brands = await brandsRes.json()
    const products = await productsRes.json()
    const brand = Array.isArray(brands) ? brands.find((b: any) => b.slug === slug) : null
    return { brand, products: products.items || [] }
  } catch {
    return { brand: null, products: [] }
  }
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const { brand } = await getBrandData(params.slug)
  if (!brand) return {}
  return {
    title: `${brand.name} Fragrances | Aurevia`,
    description: `Shop authentic ${brand.name} fragrances. Discover the full ${brand.name} collection including EDP, EDT, and Parfum concentrations.`,
    openGraph: {
      title: `${brand.name} Fragrances`,
      description: `Premium ${brand.name} fragrances collection at Aurevia.`,
    },
  }
}

export default async function BrandPage({ params }: { params: { slug: string } }) {
  const { brand, products } = await getBrandData(params.slug)

  if (!brand && products.length === 0) notFound()

  const brandName = brand?.name || params.slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())

  return (
    <div className="min-h-screen bg-obsidian pt-24 pb-16">
      <div className="container-luxury">
        {/* Brand Header */}
        <div className="mb-12 text-center">
          <p className="text-gold-400 uppercase tracking-[0.3em] text-xs mb-3">Brand Collection</p>
          <h1 className="text-5xl font-playfair text-cream mb-4">{brandName}</h1>
          {brand?.description && (
            <p className="text-obsidian-300 max-w-2xl mx-auto">{brand.description}</p>
          )}
          <p className="text-obsidian-400 text-sm mt-4">{products.length} fragrances</p>
        </div>

        {/* Product Grid */}
        <ProductGrid products={products} loading={false} />

        {/* Schema markup */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'CollectionPage',
              name: `${brandName} Fragrances`,
              description: `Shop ${brandName} fragrances at Aurevia`,
              url: `https://aurevia.com/brands/${params.slug}`,
              numberOfItems: products.length,
            }),
          }}
        />
      </div>
    </div>
  )
}
