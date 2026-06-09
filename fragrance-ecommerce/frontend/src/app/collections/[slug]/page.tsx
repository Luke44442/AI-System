import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import Image from 'next/image'
import ProductGrid from '@/components/product/ProductGrid'

async function getCollectionData(slug: string) {
  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
  try {
    const res = await fetch(`${API}/collections/${slug}`, { next: { revalidate: 3600 } })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const collection = await getCollectionData(params.slug)
  if (!collection) return {}
  return {
    title: `${collection.name} | Scentara Collections`,
    description: collection.seo_description || collection.description || `Shop the ${collection.name} fragrance collection.`,
    openGraph: {
      title: collection.seo_title || collection.name,
      description: collection.seo_description || collection.description,
      images: collection.image_url ? [collection.image_url] : [],
    },
  }
}

export default async function CollectionPage({ params }: { params: { slug: string } }) {
  const collection = await getCollectionData(params.slug)
  if (!collection) notFound()

  const products = collection.collection_products
    ?.map((cp: any) => cp.product)
    .filter(Boolean) || []

  return (
    <div className="min-h-screen bg-obsidian pt-24 pb-16">
      {/* Hero banner */}
      {collection.banner_url && (
        <div className="relative h-64 md:h-80 mb-12 overflow-hidden">
          <Image src={collection.banner_url} alt={collection.name} fill className="object-cover" />
          <div className="absolute inset-0 bg-obsidian/60 flex items-center justify-center">
            <div className="text-center">
              <h1 className="text-5xl font-playfair text-cream">{collection.name}</h1>
              {collection.description && (
                <p className="text-cream/80 mt-3 max-w-lg mx-auto">{collection.description}</p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="container-luxury">
        {!collection.banner_url && (
          <div className="mb-12 text-center">
            <p className="text-gold-400 uppercase tracking-[0.3em] text-xs mb-3">Collection</p>
            <h1 className="text-5xl font-playfair text-cream mb-4">{collection.name}</h1>
            {collection.description && (
              <p className="text-obsidian-300 max-w-2xl mx-auto">{collection.description}</p>
            )}
          </div>
        )}

        <ProductGrid products={products} loading={false} />

        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'CollectionPage',
              name: collection.name,
              description: collection.description,
              url: `https://scentara.com/collections/${params.slug}`,
            }),
          }}
        />
      </div>
    </div>
  )
}
