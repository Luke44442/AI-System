import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { productsApi, collectionsApi } from "@/lib/api";
import ProductCard from "@/components/product/ProductCard";
import type { Product, Collection } from "@/types";

export const metadata: Metadata = {
  title: "Scentara — Luxury Fragrances",
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
          <p className="section-subtitle text-gold-400 mb-6">Est. 2024</p>
          <h1 className="font-serif text-5xl md:text-7xl lg:text-8xl leading-none mb-8 text-white">
            The Art of<br />Scent
          </h1>
          <p className="text-lg md:text-xl text-gray-300 max-w-lg mx-auto mb-12 font-light leading-relaxed">
            Authentic luxury fragrances from the world's finest houses, delivered to your door.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/products" className="btn-gold text-sm">
              Explore Fragrances
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

      {/* Featured Products */}
      {featuredProducts.length > 0 && (
        <section className="py-20 bg-cream">
          <div className="container-luxury">
            <div className="text-center mb-12">
              <p className="section-subtitle text-gold-600 mb-3">Curated Selection</p>
              <h2 className="section-title">Featured Fragrances</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 lg:gap-6">
              {featuredProducts.slice(0, 8).map((product: Product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
            <div className="text-center mt-12">
              <Link href="/products" className="btn-outline">
                View All Fragrances
              </Link>
            </div>
          </div>
        </section>
      )}

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
              At Scentara, we source every fragrance directly from authorized distributors and brand partners.
              Each bottle comes with a certificate of authenticity and is inspected before shipping.
              Experience luxury the way it was meant to be experienced.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { num: "5,000+", label: "Authentic Fragrances" },
                { num: "50+", label: "Luxury Brands" },
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
          <form className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <input
              type="email"
              placeholder="Your email address"
              className="flex-1 bg-transparent border-b border-gray-600 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
            />
            <button type="submit" className="btn-gold whitespace-nowrap text-xs">
              Subscribe
            </button>
          </form>
          <p className="text-xs text-gray-600 mt-4">No spam. Unsubscribe anytime.</p>
        </div>
      </section>
    </>
  );
}
