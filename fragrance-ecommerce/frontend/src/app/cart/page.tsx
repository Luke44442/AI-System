'use client'

import { useCartStore } from '@/stores/cart'
import { formatPrice, getProductImage } from '@/lib/utils'
import Image from 'next/image'
import Link from 'next/link'

export default function CartPage() {
  const items = useCartStore((s) => s.items)
  const removeItem = useCartStore((s) => s.removeItem)
  const updateQuantity = useCartStore((s) => s.updateQuantity)
  const totalFn = useCartStore((s) => s.total)
  const total = totalFn()

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-obsidian pt-24 flex items-center justify-center">
        <div className="text-center">
          <svg className="w-16 h-16 text-obsidian-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
          <p className="text-obsidian-300 mb-2 text-lg">Your bag is empty</p>
          <p className="text-obsidian-500 text-sm mb-8">Add some fragrances to get started</p>
          <Link href="/products" className="btn-gold px-8 py-3">
            Browse Fragrances
          </Link>
        </div>
      </div>
    )
  }

  const freeShippingThreshold = 150
  const shippingCost = total >= freeShippingThreshold ? 0 : 15
  const orderTotal = total + shippingCost

  return (
    <div className="min-h-screen bg-obsidian pt-24 pb-16">
      <div className="container-luxury max-w-4xl">
        <h1 className="text-3xl font-playfair text-cream mb-8">
          Shopping Bag
          <span className="text-obsidian-400 text-lg font-normal ml-3">({items.length} items)</span>
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Items */}
          <div className="lg:col-span-2 space-y-4">
            {items.map((item) => {
              const imageUrl = getProductImage(item.product.images?.[0]?.url)
              const brandName = (item.product as any).brand?.name || ''
              const price = item.variant?.website_price ?? item.product.website_price

              return (
                <div key={`${item.product.id}-${item.variant?.id}`} className="bg-obsidian-800 rounded-lg p-4 flex gap-4 border border-obsidian-700">
                  <Link href={`/products/${item.product.slug}`} className="flex-shrink-0">
                    <div className="relative w-20 h-20 rounded overflow-hidden bg-obsidian-900">
                      <Image
                        src={imageUrl}
                        alt={`${brandName} ${item.product.name}`}
                        fill
                        className="object-cover"
                      />
                    </div>
                  </Link>

                  <div className="flex-1 min-w-0">
                    {brandName && (
                      <p className="text-gold-400 text-xs uppercase tracking-wider">{brandName}</p>
                    )}
                    <Link href={`/products/${item.product.slug}`}>
                      <p className="text-cream font-medium truncate hover:text-gold-300 transition-colors">
                        {item.product.name}
                      </p>
                    </Link>
                    {item.variant && (
                      <p className="text-obsidian-400 text-xs mt-0.5">{item.variant.name}</p>
                    )}
                    <p className="text-cream font-semibold mt-1">{formatPrice(price)}</p>
                  </div>

                  <div className="flex flex-col items-end gap-2">
                    <button
                      onClick={() => removeItem(item.id)}
                      className="text-obsidian-500 hover:text-red-400 transition-colors"
                      aria-label="Remove item"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                    <div className="flex items-center border border-obsidian-600 rounded">
                      <button
                        onClick={() => updateQuantity(item.id, item.quantity - 1)}
                        className="px-2 py-1 text-obsidian-300 hover:text-cream"
                      >
                        −
                      </button>
                      <span className="px-2 text-cream text-sm min-w-[24px] text-center">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.id, item.quantity + 1)}
                        className="px-2 py-1 text-obsidian-300 hover:text-cream"
                      >
                        +
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Summary */}
          <div className="bg-obsidian-800 rounded-lg p-6 h-fit border border-obsidian-700">
            <h2 className="text-gold-400 font-semibold uppercase tracking-wider text-sm mb-4">Order Summary</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between text-obsidian-300">
                <span>Subtotal</span>
                <span>{formatPrice(total)}</span>
              </div>
              <div className="flex justify-between text-obsidian-300">
                <span>Shipping</span>
                <span>{shippingCost === 0 ? <span className="text-green-400">Free</span> : formatPrice(shippingCost)}</span>
              </div>
              {total < freeShippingThreshold && (
                <p className="text-xs text-obsidian-400">
                  Add {formatPrice(freeShippingThreshold - total)} more for free shipping
                </p>
              )}
              <div className="flex justify-between text-cream font-semibold border-t border-obsidian-700 pt-3 mt-3">
                <span>Total</span>
                <span className="text-gold-400">{formatPrice(orderTotal)}</span>
              </div>
            </div>

            <Link href="/checkout" className="btn-gold w-full mt-6 py-3 text-center block">
              Proceed to Checkout
            </Link>
            <Link href="/products" className="text-obsidian-400 hover:text-obsidian-300 text-xs text-center block mt-3 transition-colors">
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
