import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Product, ProductVariant } from "@/types";

interface CartItem {
  id: string;
  product: Product;
  variant?: ProductVariant;
  quantity: number;
}

interface CartStore {
  items: CartItem[];
  isOpen: boolean;
  addItem: (product: Product, quantity?: number, variant?: ProductVariant) => void;
  removeItem: (itemId: string) => void;
  updateQuantity: (itemId: string, quantity: number) => void;
  clearCart: () => void;
  openCart: () => void;
  closeCart: () => void;
  toggleCart: () => void;
  total: () => number;
  itemCount: () => number;
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],
      isOpen: false,

      addItem: (product, quantity = 1, variant) => {
        set((state) => {
          const existingIdx = state.items.findIndex(
            (i) => i.product.id === product.id && i.variant?.id === variant?.id
          );
          if (existingIdx >= 0) {
            const updated = [...state.items];
            updated[existingIdx] = {
              ...updated[existingIdx],
              quantity: updated[existingIdx].quantity + quantity,
            };
            return { items: updated, isOpen: true };
          }
          return {
            items: [...state.items, { id: `${product.id}-${variant?.id || "default"}`, product, variant, quantity }],
            isOpen: true,
          };
        });
      },

      removeItem: (itemId) =>
        set((state) => ({ items: state.items.filter((i) => i.id !== itemId) })),

      updateQuantity: (itemId, quantity) =>
        set((state) => ({
          items: quantity <= 0
            ? state.items.filter((i) => i.id !== itemId)
            : state.items.map((i) => i.id === itemId ? { ...i, quantity } : i),
        })),

      clearCart: () => set({ items: [] }),
      openCart: () => set({ isOpen: true }),
      closeCart: () => set({ isOpen: false }),
      toggleCart: () => set((state) => ({ isOpen: !state.isOpen })),

      total: () => {
        const { items } = get();
        return items.reduce((sum, item) => {
          const price = item.variant?.website_price ?? item.product.website_price ?? 0;
          return sum + price * item.quantity;
        }, 0);
      },

      itemCount: () => get().items.reduce((sum, item) => sum + item.quantity, 0),
    }),
    { name: "aurevia-cart", partialize: (state) => ({ items: state.items }) }
  )
);
