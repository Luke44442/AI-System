import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { productsApi } from "@/lib/api";
import { formatPrice, concentrationLabel } from "@/lib/utils";
import ImageGallery from "@/components/product/ImageGallery";
import AddToCartButton from "./AddToCartButton";
import ProductRecommendations from "./ProductRecommendations";

interface Props { params: { slug: string } }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const product = await productsApi.get(params.slug);
    return {
      title: product.seo_title || `${product.brand?.name ?? ""} ${product.name} | Aurevia`,
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

function CheckIcon() {
  return (
    <svg className="w-4 h-4 text-gold-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

export default async function ProductPage({ params }: Props) {
  let product;
  try {
    product = await productsApi.get(params.slug);
  } catch {
    notFound();
  }

  const price = product.website_price;
  const market = product.marketplace_price;
  const compareAt = product.compare_at_price;
  // Real market comparison: our price vs the price this item lists for on
  // marketplaces (Etsy/eBay) after their fees are priced in.
  const belowMarket = price && market && market > price ? ((market - price) / market) * 100 : null;
  const condition = product.attributes?.condition ?? "New · Sealed";

  const breadcrumbs = [
    { href: "/", label: "Home" },
    { href: "/products", label: "Shop" },
    { href: `/products/${product.slug}`, label: product.name },
  ];

  return (
    <div className="pt-20 bg-obsidian">
      <div className="container-luxury py-6">
        <nav className="flex gap-2 text-xs text-white/40 mb-8" aria-label="Breadcrumb">
          {breadcrumbs.map(({ href, label }, i) => (
            <span key={href} className="flex items-center gap-2">
              {i > 0 && <span>/</span>}
              {i < breadcrumbs.length - 1 ? (
                <Link href={href} className="hover:text-cream transition-colors">{label}</Link>
              ) : (
                <span className="text-cream/80">{label}</span>
              )}
            </span>
          ))}
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16">
          {/* LEFT — gallery */}
          <ImageGallery images={product.images ?? []} productName={product.name} />

          {/* RIGHT — product intelligence */}
          <div className="lg:py-2">
            {/* Header: brand / model / SKU / authentication */}
            <div className="flex items-start justify-between gap-4">
              <div>
                {product.brand && (
                  <Link
                    href={`/products?brand_id=${product.brand.id}`}
                    className="text-xs tracking-[0.3em] uppercase text-gold-500 hover:text-gold-400 transition-colors"
                  >
                    {product.brand.name}
                  </Link>
                )}
                <h1 className="font-serif text-3xl lg:text-4xl text-cream leading-tight mt-2">{product.name}</h1>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 mt-4">
              <span className="chip border-emerald-500/40 text-emerald-400">
                <CheckIcon /> Authenticated
              </span>
              <span className="chip border-white/20 text-cream/80">{condition}</span>
              {product.concentration && (
                <span className="chip border-white/15 text-white/60">{concentrationLabel(product.concentration)}</span>
              )}
              {product.volume_ml && (
                <span className="chip border-white/15 text-white/60">{product.volume_ml}ml</span>
              )}
            </div>
            <p className="text-[11px] text-white/30 mt-3 tabular-nums">SKU {product.sku}</p>

            {/* Pricing module — financial style */}
            <div className="surface mt-6 divide-y divide-white/[0.06]">
              <div className="p-5 flex items-end justify-between">
                <div>
                  <p className="text-[10px] tracking-[0.25em] uppercase text-white/40 mb-1">Aurevia Price</p>
                  {price ? (
                    <p className="price text-4xl">{formatPrice(price)}</p>
                  ) : (
                    <p className="text-xl text-white/40">Contact for price</p>
                  )}
                </div>
                {belowMarket !== null && (
                  <div className="text-right">
                    <p className="ticker-up text-sm font-semibold">▼ {belowMarket.toFixed(1)}%</p>
                    <p className="text-[10px] tracking-[0.15em] uppercase text-white/40 mt-0.5">below market</p>
                  </div>
                )}
              </div>
              {(market || compareAt) && (
                <div className="px-5 py-3 grid grid-cols-2 gap-4 text-sm">
                  {market && (
                    <div>
                      <p className="text-[10px] tracking-[0.2em] uppercase text-white/40">Market Average</p>
                      <p className="price-sub mt-0.5">{formatPrice(market)}</p>
                    </div>
                  )}
                  {price && market && market > price && (
                    <div className="text-right">
                      <p className="text-[10px] tracking-[0.2em] uppercase text-white/40">You Save</p>
                      <p className="text-emerald-400 tabular-nums mt-0.5 font-medium">{formatPrice(market - price)}</p>
                    </div>
                  )}
                  {compareAt && price && compareAt > price && !market && (
                    <div className="text-right">
                      <p className="text-[10px] tracking-[0.2em] uppercase text-white/40">Retail</p>
                      <p className="price-sub line-through mt-0.5">{formatPrice(compareAt)}</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Availability */}
            {product.inventory_status === "low_stock" && product.inventory_quantity > 0 && (
              <p className="text-xs text-amber-400 tracking-[0.2em] uppercase mt-4">
                {product.inventory_quantity === 1
                  ? "Last one available"
                  : `Only ${product.inventory_quantity} available`}
              </p>
            )}
            {product.inventory_status === "out_of_stock" && (
              <p className="text-xs text-red-400 tracking-[0.2em] uppercase mt-4">Sold out</p>
            )}

            {/* Variants */}
            {product.variants.length > 1 && (
              <div className="mt-6">
                <p className="text-[10px] tracking-[0.25em] uppercase text-white/40 mb-3">Size</p>
                <div className="flex flex-wrap gap-2">
                  {product.variants.filter((v) => v.is_active).map((v) => (
                    <button key={v.id} className="text-sm px-4 py-2 border border-white/15 text-cream/80 hover:border-gold-500 hover:text-gold-500 transition-colors">
                      {v.volume_ml ? `${v.volume_ml}ml` : v.name}
                      {v.website_price && <span className="ml-2 text-white/40 tabular-nums">{formatPrice(v.website_price)}</span>}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Purchase area */}
            <div className="mt-6">
              <AddToCartButton product={product} />
            </div>

            {/* Trust */}
            <div className="grid grid-cols-2 gap-px bg-white/[0.06] border border-white/[0.06] mt-6">
              {[
                "Supplier Verified",
                "Authenticity Checked",
                "Secure Checkout",
                "Tracking Included",
              ].map((label) => (
                <div key={label} className="flex items-center gap-2.5 bg-charcoal-100 px-4 py-3.5">
                  <CheckIcon />
                  <span className="text-xs text-cream/80 tracking-wide">{label}</span>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-white/35 mt-3 leading-relaxed">
              Sourced from authenticated suppliers and verified before listing. Estimated delivery
              7–14 business days, fully tracked from dispatch. 30-day returns on unopened items.
            </p>

            {/* Editorial: description + composition */}
            {product.short_description && (
              <p className="text-sm text-white/60 leading-relaxed mt-8 pt-8 border-t border-white/[0.06]">
                {product.short_description}
              </p>
            )}

            {(product.top_notes || product.middle_notes || product.base_notes) && (
              <div className="mt-8 pt-8 border-t border-white/[0.06]">
                <p className="text-[10px] tracking-[0.3em] uppercase text-white/40 mb-5">Composition</p>
                <div className="space-y-4">
                  {([["Top Notes", product.top_notes], ["Heart Notes", product.middle_notes], ["Base Notes", product.base_notes]] as const)
                    .filter(([, notes]) => notes?.length)
                    .map(([label, notes]) => (
                      <div key={label} className="grid grid-cols-[100px,1fr] gap-4 items-baseline">
                        <p className="text-[10px] text-gold-500/90 uppercase tracking-[0.2em]">{label}</p>
                        <p className="text-sm text-white/60">{notes!.join(" · ")}</p>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {product.description && (
              <div className="mt-8 pt-8 border-t border-white/[0.06]">
                <p className="text-[10px] tracking-[0.3em] uppercase text-white/40 mb-4">The Story</p>
                <div className="text-sm text-white/60 leading-relaxed space-y-3">
                  {product.description.split("\n\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-8 pt-8 border-t border-white/[0.06] grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-[10px] uppercase tracking-[0.2em] text-white/35 mb-1">SKU</p>
                <p className="text-white/60 tabular-nums">{product.sku}</p>
              </div>
              {product.launch_year && (
                <div>
                  <p className="text-[10px] uppercase tracking-[0.2em] text-white/35 mb-1">Released</p>
                  <p className="text-white/60 tabular-nums">{product.launch_year}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="container-luxury pb-20">
        <ProductRecommendations productId={product.id} />
      </div>
    </div>
  );
}
