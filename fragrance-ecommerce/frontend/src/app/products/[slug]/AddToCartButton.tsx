"use client";
import { useState } from "react";
import { ShoppingBagIcon } from "@heroicons/react/24/outline";
import { useCartStore } from "@/stores/cart";
import type { Product } from "@/types";
import toast from "react-hot-toast";

export default function AddToCartButton({ product }: { product: Product }) {
  const [quantity, setQuantity] = useState(1);
  const addItem = useCartStore((s) => s.addItem);

  const handleAdd = () => {
    addItem(product, quantity);
    toast.success(`${product.name} added to bag`);
  };

  const isOutOfStock = product.inventory_status === "out_of_stock";

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="flex items-center border border-gray-200">
          <button onClick={() => setQuantity((q) => Math.max(1, q - 1))} className="px-4 py-3 hover:bg-gray-50 transition-colors text-sm">
            −
          </button>
          <span className="px-4 py-3 text-sm min-w-[3rem] text-center">{quantity}</span>
          <button onClick={() => setQuantity((q) => q + 1)} className="px-4 py-3 hover:bg-gray-50 transition-colors text-sm">
            +
          </button>
        </div>
        <button
          onClick={handleAdd}
          disabled={isOutOfStock}
          className="flex-1 btn-primary flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ShoppingBagIcon className="w-4 h-4" />
          {isOutOfStock ? "Out of Stock" : "Add to Bag"}
        </button>
      </div>
    </div>
  );
}
