"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import { ShoppingBagIcon, MagnifyingGlassIcon, UserIcon, HeartIcon, Bars3Icon, XMarkIcon, SparklesIcon } from "@heroicons/react/24/outline";
import { useCartStore } from "@/stores/cart";
import { useAuthStore } from "@/stores/auth";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/category/fragrances", label: "Fragrances" },
  { href: "/category/sneakers", label: "Sneakers" },
  { href: "/category/streetwear", label: "Streetwear" },
  { href: "/category/bags", label: "Bags" },
  { href: "/category/watches", label: "Watches" },
  { href: "/products", label: "Shop All" },
];

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const itemCount = useCartStore((s) => s.itemCount());
  const toggleCart = useCartStore((s) => s.toggleCart);
  const { customer } = useAuthStore();

  useEffect(() => {
    const handler = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <header className={cn(
      "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
      isScrolled ? "bg-obsidian/90 backdrop-blur-md border-b border-white/[0.06]" : "bg-gradient-to-b from-obsidian/80 to-transparent"
    )}>
      <nav className="container-luxury flex items-center justify-between h-16 lg:h-20">
        <button className="lg:hidden p-2 text-cream" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <XMarkIcon className="w-6 h-6" /> : <Bars3Icon className="w-6 h-6" />}
        </button>

        <Link href="/" className="font-serif text-2xl lg:text-3xl tracking-wider text-cream">
          AUREVIA
        </Link>

        <ul className="hidden lg:flex items-center gap-8">
          {NAV_LINKS.map(({ href, label }) => (
            <li key={href}>
              <Link
                href={href}
                className="text-xs tracking-widest uppercase text-cream/80 hover:text-gold-500 transition-colors"
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-4">
          <Link href="/assistant" title="AI Stylist" className="hidden sm:flex items-center gap-1 p-2 text-gold-500 hover:text-gold-400 transition-colors">
            <SparklesIcon className="w-5 h-5" />
            <span className="text-[10px] tracking-widest uppercase hidden md:inline">Stylist</span>
          </Link>
          <Link href="/search" className="hidden sm:block p-2 text-cream/80 hover:text-gold-500 transition-colors">
            <MagnifyingGlassIcon className="w-5 h-5" />
          </Link>
          <Link href={customer ? "/account/wishlist" : "/auth/login"} className="hidden sm:block p-2 text-cream/80 hover:text-gold-500 transition-colors">
            <HeartIcon className="w-5 h-5" />
          </Link>
          <Link href={customer ? "/account" : "/auth/login"} className="p-2 text-cream/80 hover:text-gold-500 transition-colors">
            <UserIcon className="w-5 h-5" />
          </Link>
          <button onClick={toggleCart} className="relative p-2 text-cream/80 hover:text-gold-500 transition-colors">
            <ShoppingBagIcon className="w-5 h-5" />
            {itemCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-gold-500 text-white text-[10px] flex items-center justify-center rounded-full font-medium">
                {itemCount > 9 ? "9+" : itemCount}
              </span>
            )}
          </button>
        </div>
      </nav>

      {mobileOpen && (
        <div className="lg:hidden bg-obsidian/95 backdrop-blur-md border-t border-white/[0.06] py-4">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="block px-6 py-3 text-sm tracking-widest uppercase text-cream/80 hover:text-gold-500 transition-colors"
              onClick={() => setMobileOpen(false)}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </header>
  );
}
