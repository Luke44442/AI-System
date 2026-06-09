import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { productsApi } from "@/lib/api";
import { getProductImage, formatPrice, concentrationLabel } from "@/lib/utils";
import AddToCartButton from "./AddToCartButton";

interface Props { params: { slug: string } }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const product = await productsApi.get(params.slug);
    return {
      title: product.seo_title || `${product.name} | Scentara`,
      description: product.seo_description || product.short_description || undefined,
      openGraph: {
        title: product.name,
        description: product.short_description || undefined,
        images: product.images?.[0]?.url ? [product.images[0].url] : [],
      },
    };
  } catch {
    return { title: "Product | Scentara" };
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
                Only {product.inventory_quantity} left in stock
              </p>
            )}

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
    </div>
  );
}
