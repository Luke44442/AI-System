import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { productsApi } from "@/lib/api";
import { getProductImage, formatPrice, concentrationLabel } from "@/lib/utils";
import AddToCartButton from "./AddToCartButton";
import ProductRecommendations from "./ProductRecommendations";

interface Props { params: { slug: string } }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const product = await productsApi.get(params.slug);
    return {
      title: product.seo_title || `${product.name} | Aurevia`,
      description: product.seo_description || product.short_description || undefined,
      openGraph: {
        title: product.name,
        description: product.short_description || undefined,
        images: product.images?.[0]?.url ? [product.images[0].url] : [],
      },
    };
  } catch {
    return { title: "Product | Aurevia" };
  }
}

export default async function ProductPage({ params }: Props) {
  let product;
  try {
    product = await productsApi.get(params.slug);
  } catch {
    notFound();
  }

  const image = getProductImage(product);
  const price = product.website_price;
  const compareAt = product.compare_at_price;
  const discount = compareAt && price ? Math.round((1 - price / compareAt) * 100) : null;

  const breadcrumbs = [
    { href: "/", label: "Home" },
    { href: "/products", label: "Fragrances" },
    { href: `/products/${product.slug}`, label: product.name },
  ];

  return (
    <div className="pt-20">
      <div className="container-luxury py-6">
        <nav className="flex gap-2 text-xs text-gray-400 mb-8">
          {breadcrumbs.map(({ href, label }, i) => (
            <span key={href} className="flex items-center gap-2">
              {i > 0 && <span>/</span>}
              {i < breadcrumbs.length - 1 ? (
                <Link href={href} className="hover:text-obsidian transition-colors">{label}</Link>
              ) : (
                <span className="text-obsidian">{label}</span>
              )}
            </span>
          ))}
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20">
          {/* Images */}
          <div className="space-y-4">
            <div className="relative aspect-square bg-cream-100 overflow-hidden">
              <Image src={image} alt={product.name} fill className="object-cover" priority />
              {discount && (
                <div className="absolute top-4 left-4 bg-gold-500 text-white text-xs px-3 py-1 tracking-wider">
                  -{discount}% OFF
                </div>
              )}
            </div>
            {product.images && product.images.length > 1 && (
              <div className="grid grid-cols-4 gap-2">
                {product.images.slice(0, 4).map((img, i) => (
                  <div key={i} className="relative aspect-square bg-cream-100 overflow-hidden cursor-pointer hover:opacity-75 transition-opacity">
                    <Image src={img.url} alt={`${product.name} ${i + 1}`} fill className="object-cover" />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Details */}
          <div className="lg:py-4">
            {product.brand && (
              <Link href={`/products?brand_id=${product.brand.id}`} className="section-subtitle text-gold-600 mb-3 block hover:text-gold-700 transition-colors">
                {product.brand.name}
              </Link>
            )}
            <h1 className="font-serif text-3xl lg:text-4xl text-obsidian leading-tight mb-4">{product.name}</h1>

            <div className="flex items-center gap-3 mb-2">
              {product.rating_avg && (
                <div className="flex items-center gap-1">
                  <span className="text-gold-500">{"★".repeat(Math.round(product.rating_avg))}</span>
                  <span className="text-xs text-gray-500">({product.review_count})</span>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2 mb-6">
              {product.concentration && (
                <span className="text-xs px-3 py-1 bg-cream-100 text-gray-600 tracking-wider">
                  {concentrationLabel(product.concentration)}
                </span>
              )}
              {product.volume_ml && (
                <span className="text-xs px-3 py-1 bg-cream-100 text-gray-600">{product.volume_ml}ml</span>
              )}
              {product.gender !== "unisex" && (
                <span className="text-xs px-3 py-1 bg-cream-100 text-gray-600 capitalize">For {product.gender}</span>
              )}
              {product.fragrance_family && (
                <span className="text-xs px-3 py-1 bg-cream-100 text-gray-600">{product.fragrance_family}</span>
              )}
            </div>

            <div className="flex items-baseline gap-3 mb-8">
              {price ? (
                <>
                  <span className="font-serif text-3xl">{formatPrice(price)}</span>
                  {compareAt && compareAt > price && (
                    <span className="text-lg text-gray-400 line-through">{formatPrice(compareAt)}</span>
                  )}
                </>
              ) : (
                <span className="font-serif text-2xl text-gray-400">Contact for price</span>
              )}
            </div>

            {product.variants.length > 1 && (
              <div className="mb-8">
                <p className="text-xs tracking-widest uppercase text-gray-500 mb-3">Size</p>
                <div className="flex flex-wrap gap-2">
                  {product.variants.filter((v) => v.is_active).map((v) => (
                    <button key={v.id} className="text-sm px-4 py-2 border border-gray-200 hover:border-obsidian transition-colors">
                      {v.volume_ml ? `${v.volume_ml}ml` : v.name}
                      {v.website_price && <span className="ml-2 text-gray-500">{formatPrice(v.website_price)}</span>}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <AddToCartButton product={product} />

            {product.inventory_status === "low_stock" && (
              <p className="text-xs text-amber-600 tracking-wider uppercase mt-3">
                {product.inventory_quantity === 1
                  ? "Last one in stock"
                  : `Only ${product.inventory_quantity} left in stock`}
              </p>
            )}

            {/* Trust + delivery */}
            <div className="mt-6 border border-gray-100 divide-y divide-gray-100">
              <div className="flex items-start gap-3 p-4">
                <svg className="w-5 h-5 text-gold-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
                <div>
                  <p className="text-xs tracking-widest uppercase text-obsidian">Authenticity Guaranteed</p>
                  <p className="text-xs text-gray-500 mt-0.5">Sourced from authenticated suppliers. Verified before listing.</p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-4">
                <svg className="w-5 h-5 text-gold-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
                </svg>
                <div>
                  <p className="text-xs tracking-widest uppercase text-obsidian">Estimated Delivery</p>
                  <p className="text-xs text-gray-500 mt-0.5">7–14 business days, fully tracked from dispatch.</p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-4">
                <svg className="w-5 h-5 text-gold-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
                </svg>
                <div>
                  <p className="text-xs tracking-widest uppercase text-obsidian">Returns</p>
                  <p className="text-xs text-gray-500 mt-0.5">30-day returns on unopened items. See policy for details.</p>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-8 border-t border-gray-100 space-y-4">
              {product.short_description && (
                <p className="text-sm text-gray-600 leading-relaxed">{product.short_description}</p>
              )}
            </div>

            {(product.top_notes || product.middle_notes || product.base_notes) && (
              <div className="mt-8 pt-8 border-t border-gray-100">
                <p className="text-xs tracking-widest uppercase text-gray-500 mb-6">Fragrance Profile</p>
                <div className="space-y-4">
                  {product.top_notes?.length ? (
                    <div>
                      <p className="text-xs text-gold-600 uppercase tracking-widest mb-2">Top Notes</p>
                      <p className="text-sm text-gray-600">{product.top_notes.join(" · ")}</p>
                    </div>
                  ) : null}
                  {product.middle_notes?.length ? (
                    <div>
                      <p className="text-xs text-gold-600 uppercase tracking-widest mb-2">Heart Notes</p>
                      <p className="text-sm text-gray-600">{product.middle_notes.join(" · ")}</p>
                    </div>
                  ) : null}
                  {product.base_notes?.length ? (
                    <div>
                      <p className="text-xs text-gold-600 uppercase tracking-widest mb-2">Base Notes</p>
                      <p className="text-sm text-gray-600">{product.base_notes.join(" · ")}</p>
                    </div>
                  ) : null}
                </div>
              </div>
            )}

            {product.description && (
              <div className="mt-8 pt-8 border-t border-gray-100">
                <p className="text-xs tracking-widest uppercase text-gray-500 mb-4">About This Fragrance</p>
                <div className="text-sm text-gray-600 leading-relaxed space-y-3">
                  {product.description.split("\n\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-8 pt-8 border-t border-gray-100">
              <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-400 mb-1">SKU</p>
                  <p>{product.sku}</p>
                </div>
                {product.launch_year && (
                  <div>
                    <p className="text-xs uppercase tracking-wider text-gray-400 mb-1">Year</p>
                    <p>{product.launch_year}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container-luxury pb-16">
        <ProductRecommendations productId={product.id} />
      </div>
    </div>
  );
}
