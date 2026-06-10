import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { productsApi, collectionsApi } from "@/lib/api";
import ProductCard from "@/components/product/ProductCard";
import NewsletterForm from "@/components/NewsletterForm";
import RecommendationRow from "@/components/product/RecommendationRow";
import { recommendationsApi } from "@/lib/api";
import type { Product, Collection } from "@/types";

export const metadata: Metadata = {
  title: "Aurevia — Luxury Fragrances",
  description: "Authentic luxury fragrances from the world's finest houses. Free shipping on orders over $75.",
};

export const revalidate = 3600;

async function getHomeData() {
  try {
    const [featuredProducts, collections] = await Promise.all([
      productsApi.getFeatured(),
      collectionsApi.list(),
    ]);
    return { featuredProducts: featuredProducts.items, collections };
  } catch {
    return { featuredProducts: [], collections: [] };
  }
}

export default async function HomePage() {
  const { featuredProducts, collections } = await getHomeData();

  return (
    <>
      {/* Hero */}
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-obsidian">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-obsidian/20 to-obsidian/60" />
        </div>
        <div className="relative z-10 text-center text-white px-4">
          <p className="section-subtitle text-gold-400 mb-6">Est. 2024 · Luxury Marketplace</p>
          <h1 className="font-serif text-5xl md:text-7xl lg:text-8xl leading-none mb-8 text-white">
            Luxury,<br />Curated
          </h1>
          <p className="text-lg md:text-xl text-gray-300 max-w-xl mx-auto mb-12 font-light leading-relaxed">
            Authentic fragrances, sneakers, streetwear, and designer pieces from the world's finest houses — delivered to your door.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/products" className="btn-gold text-sm">
              Shop All
            </Link>
            <Link href="/collections" className="btn-outline border-white text-white hover:bg-white hover:text-obsidian text-sm">
              View Collections
            </Link>
          </div>
        </div>
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-white/60">
          <div className="w-px h-12 bg-white/30 animate-pulse" />
          <span className="text-[10px] tracking-widest uppercase">Scroll</span>
        </div>
      </section>

      {/* Trust Badges */}
      <section className="bg-obsidian text-white py-6">
        <div className="container-luxury">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {[
              { label: "Authentic", sub: "100% Genuine Products" },
              { label: "Free Shipping", sub: "On Orders Over $75" },
              { label: "Easy Returns", sub: "30-Day Return Policy" },
              { label: "Secure Payment", sub: "Stripe Encrypted" },
            ].map(({ label, sub }) => (
              <div key={label} className="py-2">
                <p className="text-xs tracking-widest uppercase text-gold-400 mb-1">{label}</p>
                <p className="text-xs text-gray-400">{sub}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Shop by Category */}
      <section className="py-20 bg-white">
        <div className="container-luxury">
          <div className="text-center mb-12">
            <p className="section-subtitle text-gold-600 mb-3">Explore</p>
            <h2 className="section-title">Shop by Category</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 lg:gap-6">
            {[
              { slug: "fragrances", label: "Fragrances", img: "https://images.unsplash.com/photo-1541643600914-78b084683601?w=600&q=80" },
              { slug: "sneakers", label: "Sneakers", img: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80" },
              { slug: "streetwear", label: "Streetwear", img: "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&q=80" },
              { slug: "designer-clothing", label: "Designer Clothing", img: "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600&q=80" },
              { slug: "bags", label: "Bags", img: "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=600&q=80" },
              { slug: "watches", label: "Watches", img: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80" },
              { slug: "accessories", label: "Accessories", img: "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600&q=80" },
              { slug: "jewelry", label: "Jewelry", img: "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=600&q=80" },
            ].map((cat) => (
              <Link
                key={cat.slug}
                href={`/category/${cat.slug}`}
                className="group relative aspect-square overflow-hidden bg-obsidian flex items-end p-5"
              >
                <Image
                  src={cat.img}
                  alt={cat.label}
                  fill
                  className="object-cover opacity-70 group-hover:opacity-50 group-hover:scale-105 transition-all duration-700"
                />
                <span className="relative z-10 font-serif text-xl text-white">{cat.label}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      {featuredProducts.length > 0 && (
        <section className="py-20 bg-cream">
          <div className="container-luxury">
            <div className="text-center mb-12">
              <p className="section-subtitle text-gold-600 mb-3">Curated Selection</p>
              <h2 className="section-title">Featured</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 lg:gap-6">
              {featuredProducts.slice(0, 8).map((product: Product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
            <div className="text-center mt-12">
              <Link href="/products" className="btn-outline">
                Shop All
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* Trending Now */}
      <section className="py-12 bg-cream">
        <div className="container-luxury">
          <RecommendationRow
            title="Trending Now"
            subtitle="What Aurevia shoppers are loving"
            load={() => recommendationsApi.trending(8)}
          />
        </div>
      </section>

      {/* Collections */}
      {collections.length > 0 && (
        <section className="py-20 bg-white">
          <div className="container-luxury">
            <div className="text-center mb-12">
              <p className="section-subtitle text-gold-600 mb-3">Themed Curation</p>
              <h2 className="section-title">Our Collections</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {collections.slice(0, 6).map((col: Collection) => (
                <Link
                  key={col.id}
                  href={`/collections/${col.slug}`}
                  className="group relative aspect-[4/3] overflow-hidden bg-obsidian flex items-end p-6"
                >
                  {col.image_url && (
                    <Image
                      src={col.image_url}
                      alt={col.name}
                      fill
                      className="object-cover opacity-60 group-hover:opacity-40 group-hover:scale-105 transition-all duration-700"
                    />
                  )}
                  <div className="relative z-10 text-white">
                    <p className="font-serif text-2xl mb-1">{col.name}</p>
                    {col.description && (
                      <p className="text-xs text-gray-300 line-clamp-2">{col.description}</p>
                    )}
                    <p className="text-xs tracking-widest uppercase text-gold-400 mt-3">Explore →</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Brand Promise */}
      <section className="py-20 bg-cream-100">
        <div className="container-luxury">
          <div className="max-w-3xl mx-auto text-center">
            <p className="section-subtitle text-gold-600 mb-6">Our Promise</p>
            <h2 className="section-title mb-8">Every Bottle, Authenticated</h2>
            <p className="text-gray-600 leading-relaxed mb-12">
              At Aurevia, every piece is sourced from trusted partners and inspected before it ships.
              From fragrances to sneakers to designer apparel, each item is verified for authenticity
              so you can shop luxury with total confidence.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { num: "5,000+", label: "Authenticated Products" },
                { num: "60+", label: "Luxury Brands" },
                { num: "98%", label: "Customer Satisfaction" },
              ].map(({ num, label }) => (
                <div key={label} className="text-center">
                  <p className="font-serif text-4xl text-gold-500 mb-2">{num}</p>
                  <p className="text-xs tracking-widest uppercase text-gray-500">{label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Newsletter */}
      <section className="py-20 bg-obsidian text-white">
        <div className="container-luxury max-w-2xl mx-auto text-center">
          <p className="section-subtitle text-gold-400 mb-4">Exclusive Access</p>
          <h2 className="font-serif text-4xl text-white mb-4">Join the Inner Circle</h2>
          <p className="text-gray-400 mb-8 text-sm leading-relaxed">
            Be first to discover new arrivals, exclusive launches, and members-only discounts.
          </p>
          <NewsletterForm />
          <p className="text-xs text-gray-600 mt-4">No spam. Unsubscribe anytime.</p>
        </div>
      </section>
    </>
  );
}
