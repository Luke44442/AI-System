"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShoppingBagIcon, HeartIcon } from "@heroicons/react/24/outline";
import { useCartStore } from "@/stores/cart";
import type { Product } from "@/types";
import toast from "react-hot-toast";

export default function AddToCartButton({ product }: { product: Product }) {
  const [quantity, setQuantity] = useState(1);
  const addItem = useCartStore((s) => s.addItem);
  const router = useRouter();

  const isOutOfStock = product.inventory_status === "out_of_stock";

  const handleAdd = () => {
    addItem(product, quantity);
    toast.success(`${product.name} added to bag`);
  };

  const handleBuyNow = () => {
    addItem(product, quantity);
    router.push("/checkout");
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="flex items-center border border-white/15">
          <button onClick={() => setQuantity((q) => Math.max(1, q - 1))} className="px-4 py-3.5 text-cream/70 hover:bg-white/5 transition-colors text-sm" aria-label="Decrease quantity">
            −
          </button>
          <span className="px-3 py-3.5 text-sm min-w-[2.5rem] text-center tabular-nums">{quantity}</span>
          <button onClick={() => setQuantity((q) => q + 1)} className="px-4 py-3.5 text-cream/70 hover:bg-white/5 transition-colors text-sm" aria-label="Increase quantity">
            +
          </button>
        </div>
        <button
          onClick={handleBuyNow}
          disabled={isOutOfStock}
          className="flex-1 bg-gold-500 text-obsidian py-3.5 text-sm tracking-[0.2em] uppercase font-semibold hover:bg-gold-400 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isOutOfStock ? "Sold Out" : "Buy Now"}
        </button>
      </div>
      <div className="flex gap-3">
        <button
          onClick={handleAdd}
          disabled={isOutOfStock}
          className="flex-1 border border-white/20 text-cream py-3 text-xs tracking-[0.2em] uppercase font-medium hover:border-gold-500 hover:text-gold-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <ShoppingBagIcon className="w-4 h-4" />
          Add to Bag
        </button>
        <button
          onClick={() => toast.success("Saved to wishlist")}
          className="px-5 border border-white/20 text-cream/80 hover:border-gold-500 hover:text-gold-500 transition-colors flex items-center justify-center"
          aria-label="Add to wishlist"
        >
          <HeartIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
