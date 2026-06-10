import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import CategoryBrowser from '@/components/category/CategoryBrowser'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

async function getCategory(slug: string) {
  try {
    const res = await fetch(`${API}/categories`, { next: { revalidate: 3600 } })
    if (!res.ok) return null
    const categories = await res.json()
    const flat: any[] = []
    const walk = (list: any[]) => list?.forEach((c) => { flat.push(c); if (c.children) walk(c.children) })
    walk(Array.isArray(categories) ? categories : [])
    return flat.find((c) => c.slug === slug) || null
  } catch {
    return null
  }
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const category = await getCategory(params.slug)
  const name = category?.name || params.slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())
  return {
    title: `${name} | Aurevia`,
    description: category?.description || `Shop authentic luxury ${name.toLowerCase()} at Aurevia. Verified, inspected, and delivered worldwide.`,
    openGraph: {
      title: `${name} | Aurevia`,
      description: category?.description || `Shop authentic luxury ${name.toLowerCase()} at Aurevia.`,
      images: category?.image_url ? [category.image_url] : [],
    },
  }
}

export default async function CategoryPage({ params }: { params: { slug: string } }) {
  const category = await getCategory(params.slug)
  // Allow rendering even if the category lookup fails (browser fetches its own data),
  // but 404 only for clearly unknown slugs handled client-side.
  const name = category?.name || params.slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())

  if (!params.slug) notFound()

  return (
    <div className="min-h-screen bg-white pt-24 pb-16">
      <div className="container-luxury">
        {/* Header */}
        <div className="text-center mb-12">
          <p className="section-subtitle text-gold-600 mb-3">Aurevia</p>
          <h1 className="section-title">{name}</h1>
          {category?.description && (
            <p className="text-gray-500 max-w-2xl mx-auto mt-4">{category.description}</p>
          )}
        </div>

        <CategoryBrowser categorySlug={params.slug} />

        {/* SEO structured data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'CollectionPage',
              name: `${name} — Aurevia`,
              description: category?.description || `Shop luxury ${name.toLowerCase()} at Aurevia.`,
              url: `https://aurevia.com/category/${params.slug}`,
            }),
          }}
        />
      </div>
    </div>
  )
}
