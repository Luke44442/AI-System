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

export default function ProductCard({ product, className }: ProductCardProps) {
  const [wishListed, setWishlisted] = useState(false);
  const [imgIdx, setImgIdx] = useState(0);
  const addItem = useCartStore((s) => s.addItem);

  const price = product.website_price;
  const compareAt = product.compare_at_price;
  const discount = compareAt && price ? Math.round((1 - price / compareAt) * 100) : null;
  const image = getProductImage(product, imgIdx);
  const hoverImage = product.images?.[1]?.url;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("group card-product", className)}
    >
      <div className="relative aspect-[3/4] overflow-hidden bg-cream-100">
        <Link href={`/products/${product.slug}`}>
          <Image
            src={image}
            alt={product.name}
            fill
            sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
            className={cn(
              "object-cover transition-all duration-700",
              hoverImage ? "group-hover:opacity-0" : "group-hover:scale-105"
            )}
            onError={() => setImgIdx(0)}
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

        {discount && (
          <div className="absolute top-3 left-3 bg-gold-500 text-white text-[10px] px-2 py-1 tracking-wider">
            -{discount}%
          </div>
        )}
        {product.is_new_arrival && !discount && (
          <div className="absolute top-3 left-3 bg-obsidian text-white text-[10px] px-2 py-1 tracking-wider">
            NEW
          </div>
        )}

        <button
          onClick={() => setWishlisted(!wishListed)}
          className="absolute top-3 right-3 p-2 bg-white/80 backdrop-blur-sm rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white"
        >
          {wishListed
            ? <HeartSolid className="w-4 h-4 text-red-500" />
            : <HeartIcon className="w-4 h-4 text-obsidian" />}
        </button>

        {product.inventory_status !== "out_of_stock" && (
          <button
            onClick={() => addItem(product)}
            className="absolute bottom-0 left-0 right-0 bg-obsidian text-white text-xs tracking-widest uppercase py-3 translate-y-full group-hover:translate-y-0 transition-transform duration-300 flex items-center justify-center gap-2"
          >
            <ShoppingBagIcon className="w-4 h-4" />
            Add to Bag
          </button>
        )}
      </div>

      <div className="p-4">
        {product.brand && (
          <p className="text-[10px] tracking-widest uppercase text-gold-600 mb-1">{product.brand.name}</p>
        )}
        <Link href={`/products/${product.slug}`}>
          <h3 className="font-serif text-sm font-medium text-obsidian hover:text-gold-600 transition-colors line-clamp-2 leading-snug">
            {product.name}
          </h3>
        </Link>
        <p className="text-xs text-gray-500 mt-1">
          {[concentrationLabel(product.concentration), product.volume_ml ? `${product.volume_ml}ml` : null]
            .filter(Boolean).join(" · ")}
        </p>
        <div className="mt-2 flex items-baseline gap-2">
          {price ? (
            <>
              <span className="text-sm font-medium">{formatPrice(price)}</span>
              {compareAt && compareAt > price && (
                <span className="text-xs text-gray-400 line-through">{formatPrice(compareAt)}</span>
              )}
            </>
          ) : (
            <span className="text-sm text-gray-400">Price on request</span>
          )}
        </div>
        {product.inventory_status === "out_of_stock" && (
          <p className="text-[10px] text-red-500 tracking-wider uppercase mt-1">Out of Stock</p>
        )}
        {product.inventory_status === "low_stock" && (
          <p className="text-[10px] text-amber-600 tracking-wider uppercase mt-1">
            {product.inventory_quantity === 1
              ? "Last one — 1 left"
              : product.inventory_quantity > 0 && product.inventory_quantity <= 5
                ? `Only ${product.inventory_quantity} left`
                : "Low Stock"}
          </p>
        )}
      </div>
    </motion.div>
  );
}
