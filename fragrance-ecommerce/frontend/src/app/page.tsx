import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { productsApi, collectionsApi } from "@/lib/api";
import { getProductImage, formatPrice } from "@/lib/utils";
import ProductCard from "@/components/product/ProductCard";
import NewsletterForm from "@/components/NewsletterForm";
import RecommendationRow from "@/components/product/RecommendationRow";
import type { Product, Collection } from "@/types";

export const metadata: Metadata = {
  title: "Aurevia — Authentic Luxury, Intelligently Sourced",
  description: "Authenticated luxury fragrances, sneakers, streetwear and designer pieces — priced below market, tracked to your door.",
};

export const revalidate = 3600;

const CATEGORIES = [
  { slug: "fragrances", label: "Fragrances", img: "/demo/cat-fragrances.jpg" },
  { slug: "sneakers", label: "Sneakers", img: "/demo/cat-sneakers.jpg" },
  { slug: "streetwear", label: "Streetwear", img: "/demo/cat-streetwear.jpg" },
  { slug: "designer-clothing", label: "Designer", img: "/demo/cat-designer.jpg" },
  { slug: "bags", label: "Bags", img: "/demo/cat-bags.jpg" },
  { slug: "watches", label: "Watches", img: "/demo/cat-watches.jpg" },
  { slug: "accessories", label: "Accessories", img: "/demo/cat-accessories.jpg" },
  { slug: "jewelry", label: "Jewelry", img: "/demo/cat-jewelry.jpg" },
];

async function getHomeData() {
  try {
    const [featuredProducts, collections] = await Promise.all([
      productsApi.getFeatured(),
      collectionsApi.list(),
    ]);
    return { featuredProducts: featuredProducts.items, collections };
  } catch {
    return { featuredProducts: [] as Product[], collections: [] as Collection[] };
  }
}

export default async function HomePage() {
  const { featuredProducts, collections } = await getHomeData();
  const hero = featuredProducts[0];

  return (
    <>
      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center overflow-hidden bg-obsidian">
        {/* ambient gold glow */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden>
          <div className="absolute -top-1/3 left-1/2 -translate-x-1/2 w-[900px] h-[900px] rounded-full bg-gold-500/[0.06] blur-3xl" />
        </div>

        <div className="container-luxury relative z-10 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center pt-24 pb-16">
          <div className="animate-slide-up">
            <p className="section-subtitle mb-6">Authenticated Resale Marketplace</p>
            <h1 className="font-serif text-5xl md:text-6xl xl:text-7xl leading-[1.05] text-cream">
              Authentic Luxury.
              <br />
              <span className="text-gold-500">Intelligently</span> Sourced.
            </h1>
            <p className="mt-8 text-base md:text-lg text-white/50 max-w-md font-light leading-relaxed">
              Every piece verified at the source, priced against live market data,
              and tracked from supplier to your door.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4">
              <Link href="/products" className="btn-gold text-center">Explore Collection</Link>
              <Link href="/products?is_new_arrival=true" className="btn-outline text-center">View Latest Drops</Link>
            </div>

            {/* category quick-nav */}
            <div className="mt-14 flex flex-wrap gap-x-6 gap-y-2">
              {CATEGORIES.slice(0, 6).map((c) => (
                <Link
                  key={c.slug}
                  href={`/category/${c.slug}`}
                  className="text-[11px] tracking-[0.25em] uppercase text-white/40 hover:text-gold-500 transition-colors"
                >
                  {c.label}
                </Link>
              ))}
            </div>
          </div>

          {/* featured product stage */}
          {hero && (
            <Link href={`/products/${hero.slug}`} className="relative group animate-fade-in hidden lg:block">
              <div className="relative aspect-[3/4] max-w-md ml-auto surface overflow-hidden">
                <Image
                  src={getProductImage(hero)}
                  alt={hero.name}
                  fill
                  priority
                  sizes="(max-width: 1024px) 0px, 40vw"
                  className="object-cover transition-transform duration-[1.2s] group-hover:scale-[1.03]"
                />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-obsidian/95 via-obsidian/60 to-transparent p-6 pt-16">
                  <p className="text-[10px] tracking-[0.25em] uppercase text-gold-500">{hero.brand?.name}</p>
                  <div className="flex items-end justify-between mt-1">
                    <p className="font-serif text-2xl text-cream">{hero.name}</p>
                    {hero.website_price && <p className="price text-xl">{formatPrice(hero.website_price)}</p>}
                  </div>
                  {hero.marketplace_price && hero.website_price && hero.marketplace_price > hero.website_price && (
                    <p className="ticker-up text-[11px] mt-1">
                      ▼ {(((hero.marketplace_price - hero.website_price) / hero.marketplace_price) * 100).toFixed(1)}% below market avg
                    </p>
                  )}
                </div>
              </div>
            </Link>
          )}
        </div>

        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-white/30" aria-hidden>
          <div className="w-px h-10 bg-white/20 animate-pulse" />
          <span className="text-[9px] tracking-[0.3em] uppercase">Scroll</span>
        </div>
      </section>

      {/* ── Assurance strip ────────────────────────────────────────────── */}
      <section className="border-y border-white/[0.06] bg-charcoal-200">
        <div className="container-luxury grid grid-cols-2 md:grid-cols-4 divide-x divide-white/[0.06]">
          {[
            { label: "Authenticated", sub: "Verified at the source" },
            { label: "Below Market", sub: "Priced against live data" },
            { label: "Fully Tracked", sub: "Supplier to doorstep" },
            { label: "Secure Checkout", sub: "Stripe encrypted" },
          ].map(({ label, sub }) => (
            <div key={label} className="py-6 px-4 text-center">
              <p className="text-[11px] tracking-[0.25em] uppercase text-gold-500">{label}</p>
              <p className="text-xs text-white/40 mt-1">{sub}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Featured drops ─────────────────────────────────────────────── */}
      {featuredProducts.length > 0 && (
        <section className="py-20 bg-obsidian">
          <div className="container-luxury">
            <div className="flex items-end justify-between mb-10">
              <div>
                <p className="section-subtitle mb-3">Featured Drops</p>
                <h2 className="section-title">Current Selection</h2>
              </div>
              <Link href="/products" className="hidden sm:block text-xs tracking-[0.25em] uppercase text-white/50 hover:text-gold-500 transition-colors">
                View All →
              </Link>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 lg:gap-6">
              {featuredProducts.slice(0, 8).map((product: Product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Shop by category ───────────────────────────────────────────── */}
      <section className="py-20 bg-charcoal-200 border-y border-white/[0.06]">
        <div className="container-luxury">
          <div className="text-center mb-12">
            <p className="section-subtitle mb-3">Explore</p>
            <h2 className="section-title">Shop by Category</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 lg:gap-4">
            {CATEGORIES.map((cat) => (
              <Link
                key={cat.slug}
                href={`/category/${cat.slug}`}
                className="group relative aspect-square overflow-hidden bg-obsidian border border-white/[0.06] hover:border-gold-500/40 transition-colors flex items-end p-5"
              >
                <Image
                  src={cat.img}
                  alt={cat.label}
                  fill
                  sizes="(max-width: 768px) 50vw, 25vw"
                  className="object-cover opacity-60 group-hover:opacity-40 group-hover:scale-[1.04] transition-all duration-700"
                />
                <span className="relative z-10 font-serif text-xl text-cream">{cat.label}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── Trending ───────────────────────────────────────────────────── */}
      <section className="py-12 bg-obsidian">
        <div className="container-luxury">
          <RecommendationRow
            title="Trending Now"
            subtitle="What Aurevia collectors are watching"
            source={{ kind: "trending", limit: 8 }}
          />
        </div>
      </section>

      {/* ── Collections ────────────────────────────────────────────────── */}
      {collections.length > 0 && (
        <section className="py-20 bg-charcoal-200 border-y border-white/[0.06]">
          <div className="container-luxury">
            <div className="text-center mb-12">
              <p className="section-subtitle mb-3">Curated</p>
              <h2 className="section-title">Collections</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {collections.slice(0, 6).map((col: Collection) => (
                <Link
                  key={col.id}
                  href={`/collections/${col.slug}`}
                  className="group relative aspect-[4/3] overflow-hidden bg-obsidian border border-white/[0.06] hover:border-gold-500/40 transition-colors flex items-end p-6"
                >
                  {col.image_url && (
                    <Image
                      src={col.image_url}
                      alt={col.name}
                      fill
                      sizes="(max-width: 768px) 100vw, 33vw"
                      className="object-cover opacity-50 group-hover:opacity-35 group-hover:scale-[1.04] transition-all duration-700"
                    />
                  )}
                  <div className="relative z-10">
                    <p className="font-serif text-2xl text-cream mb-1">{col.name}</p>
                    {col.description && (
                      <p className="text-xs text-white/50 line-clamp-2">{col.description}</p>
                    )}
                    <p className="text-[10px] tracking-[0.3em] uppercase text-gold-500 mt-3">Explore →</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Promise ────────────────────────────────────────────────────── */}
      <section className="py-24 bg-obsidian">
        <div className="container-luxury max-w-3xl mx-auto text-center">
          <p className="section-subtitle mb-6">Our Standard</p>
          <h2 className="section-title mb-8">Every Piece, Authenticated</h2>
          <p className="text-white/50 leading-relaxed mb-14 font-light">
            Aurevia sits between trusted suppliers and the open market. Each item is sourced from
            verified partners, checked before it ships, and priced against live marketplace data —
            so what you pay is grounded in what the market says it's worth.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {[
              { num: "5,000+", label: "Authenticated Products" },
              { num: "60+", label: "Luxury Brands" },
              { num: "98%", label: "Customer Satisfaction" },
            ].map(({ num, label }) => (
              <div key={label}>
                <p className="font-serif text-4xl text-gold-500 mb-2 tabular-nums">{num}</p>
                <p className="text-[10px] tracking-[0.25em] uppercase text-white/40">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Newsletter ─────────────────────────────────────────────────── */}
      <section className="py-20 bg-charcoal-200 border-t border-white/[0.06]">
        <div className="container-luxury max-w-2xl mx-auto text-center">
          <p className="section-subtitle mb-4">Private Access</p>
          <h2 className="font-serif text-4xl text-cream mb-4">Join the Inner Circle</h2>
          <p className="text-white/40 mb-8 text-sm leading-relaxed">
            New drops, price movements, and members-only releases — before anyone else.
          </p>
          <NewsletterForm />
          <p className="text-xs text-white/25 mt-4">No spam. Unsubscribe anytime.</p>
        </div>
      </section>
    </>
  );
}
