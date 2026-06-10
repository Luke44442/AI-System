"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import { ShoppingBagIcon, MagnifyingGlassIcon, UserIcon, HeartIcon, Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";
import { useCartStore } from "@/stores/cart";
import { useAuthStore } from "@/stores/auth";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/products", label: "All Fragrances" },
  { href: "/collections", label: "Collections" },
  { href: "/products?gender=male", label: "For Him" },
  { href: "/products?gender=female", label: "For Her" },
  { href: "/products?is_featured=true", label: "Featured" },
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
      isScrolled ? "bg-white/95 backdrop-blur-sm shadow-sm" : "bg-transparent"
    )}>
      <nav className="container-luxury flex items-center justify-between h-16 lg:h-20">
        <button className="lg:hidden p-2" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <XMarkIcon className="w-6 h-6" /> : <Bars3Icon className="w-6 h-6" />}
        </button>

        <Link href="/" className="font-serif text-2xl lg:text-3xl tracking-wider text-obsidian">
          AUREVIA
        </Link>

        <ul className="hidden lg:flex items-center gap-8">
          {NAV_LINKS.map(({ href, label }) => (
            <li key={href}>
              <Link
                href={href}
                className="text-xs tracking-widest uppercase text-obsidian hover:text-gold-500 transition-colors"
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-4">
          <Link href="/search" className="hidden sm:block p-2 hover:text-gold-500 transition-colors">
            <MagnifyingGlassIcon className="w-5 h-5" />
          </Link>
          <Link href={customer ? "/account/wishlist" : "/auth/login"} className="hidden sm:block p-2 hover:text-gold-500 transition-colors">
            <HeartIcon className="w-5 h-5" />
          </Link>
          <Link href={customer ? "/account" : "/auth/login"} className="p-2 hover:text-gold-500 transition-colors">
            <UserIcon className="w-5 h-5" />
          </Link>
          <button onClick={toggleCart} className="relative p-2 hover:text-gold-500 transition-colors">
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
        <div className="lg:hidden bg-white border-t border-gray-100 py-4">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="block px-6 py-3 text-sm tracking-widest uppercase hover:text-gold-500 transition-colors"
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
