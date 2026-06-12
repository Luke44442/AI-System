"use client";
import Image from "next/image";
import Link from "next/link";
import { HeartIcon, ShoppingBagIcon } from "@heroicons/react/24/outline";
import { HeartIcon as HeartSolid } from "@heroicons/react/24/solid";
import { useState } from "react";
import { motion } from "framer-motion";
import { cn, formatPrice, getProductImage, concentrationLabel } from "@/lib/utils";
import { useCartStore } from "@/stores/cart";
import type { Product } from "@/types";

interface ProductCardProps {
  product: Product;
  className?: string;
}

/** Percentage our price sits below the marketplace average — real data
 *  (website_price vs marketplace_price), shown StockX-style. */
function marketDelta(product: Product): number | null {
  const ours = product.website_price;
  const market = product.marketplace_price;
  if (!ours || !market || market <= ours) return null;
  return ((market - ours) / market) * 100;
}

export default function ProductCard({ product, className }: ProductCardProps) {
  const [wishListed, setWishlisted] = useState(false);
  const addItem = useCartStore((s) => s.addItem);

  const price = product.website_price;
  const compareAt = product.compare_at_price;
  const image = getProductImage(product);
  const hoverImage = product.images?.[1]?.url;
  const delta = marketDelta(product);
  const condition = product.attributes?.condition ?? "New";
  const qty = product.inventory_quantity;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={cn("group card-product", className)}
    >
      <div className="relative aspect-[3/4] overflow-hidden bg-charcoal-300">
        <Link href={`/products/${product.slug}`}>
          <Image
            src={image}
            alt={product.name}
            fill
            sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
            className={cn(
              "object-cover transition-all duration-700",
              hoverImage ? "group-hover:opacity-0" : "group-hover:scale-[1.04]"
            )}
          />
          {hoverImage && (
            <Image
              src={hoverImage}
              alt={`${product.name} alternate`}
              fill
              sizes="(max-width: 768px) 50vw, 33vw"
              className="object-cover opacity-0 group-hover:opacity-100 transition-opacity duration-700"
            />
          )}
        </Link>

        {/* Condition + state chips */}
        <div className="absolute top-3 left-3 flex flex-col gap-1.5">
          <span className="chip border-white/20 bg-obsidian/70 backdrop-blur-sm text-cream/90">
            {condition}
          </span>
          {product.is_new_arrival && (
            <span className="chip border-gold-500/40 bg-obsidian/70 backdrop-blur-sm text-gold-500">
              New Drop
            </span>
          )}
        </div>

        <button
          aria-label="Add to wishlist"
          onClick={() => setWishlisted(!wishListed)}
          className="absolute top-3 right-3 p-2 bg-obsidian/60 backdrop-blur-sm rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-obsidian"
        >
          {wishListed
            ? <HeartSolid className="w-4 h-4 text-gold-500" />
            : <HeartIcon className="w-4 h-4 text-cream" />}
        </button>

        {product.inventory_status !== "out_of_stock" && (
          <button
            onClick={() => addItem(product)}
            className="absolute bottom-0 left-0 right-0 bg-gold-500 text-obsidian text-xs tracking-widest uppercase font-semibold py-3 translate-y-full group-hover:translate-y-0 transition-transform duration-300 flex items-center justify-center gap-2"
          >
            <ShoppingBagIcon className="w-4 h-4" />
            Add to Bag
          </button>
        )}
      </div>

      <div className="p-4">
        {product.brand && (
          <p className="text-[10px] tracking-[0.2em] uppercase text-gold-500/90 mb-1">{product.brand.name}</p>
        )}
        <Link href={`/products/${product.slug}`}>
          <h3 className="font-serif text-sm font-medium text-cream hover:text-gold-500 transition-colors line-clamp-2 leading-snug">
            {product.name}
          </h3>
        </Link>
        <p className="text-xs text-white/40 mt-1">
          {[concentrationLabel(product.concentration), product.volume_ml ? `${product.volume_ml}ml` : null]
            .filter(Boolean).join(" · ")}
        </p>

        {/* Financial-style price row */}
        <div className="mt-3 flex items-baseline justify-between gap-2">
          {price ? (
            <span className="price text-base">{formatPrice(price)}</span>
          ) : (
            <span className="text-sm text-white/40">Price on request</span>
          )}
          {delta !== null && (
            <span className="ticker-up text-[11px] font-medium" title="Below current marketplace average">
              ▼ {delta.toFixed(1)}% vs market
            </span>
          )}
          {delta === null && compareAt && price && compareAt > price && (
            <span className="price-sub text-xs line-through">{formatPrice(compareAt)}</span>
          )}
        </div>

        {/* Availability — real inventory, no fake scarcity */}
        {product.inventory_status === "out_of_stock" && (
          <p className="text-[10px] text-red-400 tracking-[0.15em] uppercase mt-2">Sold Out</p>
        )}
        {product.inventory_status === "low_stock" && qty > 0 && qty <= 5 && (
          <p className="text-[10px] text-amber-400 tracking-[0.15em] uppercase mt-2">
            {qty === 1 ? "Last one available" : `Only ${qty} available`}
          </p>
        )}
      </div>
    </motion.div>
  );
}
