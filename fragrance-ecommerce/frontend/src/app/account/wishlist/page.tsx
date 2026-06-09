'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'
import { wishlistApi } from '@/lib/api'
import { formatPrice, getProductImage } from '@/lib/utils'
import Image from 'next/image'
import toast from 'react-hot-toast'
import type { Product } from '@/types'

export default function WishlistPage() {
  const router = useRouter()
  const user = useAuthStore((s) => s.user)
  const addItem = useCartStore((s) => s.addItem)
  const [wishlist, setWishlist] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { router.push('/auth/login'); return }
    fetchWishlist()
  }, [user])

  const fetchWishlist = async () => {
    setLoading(true)
    try {
      const res = await wishlistApi.get()
      setWishlist(res?.items?.map((item: any) => item.product) || [])
    } catch {
      setWishlist([])
    } finally {
      setLoading(false)
    }
  }

  const removeFromWishlist = async (productId: string) => {
    try {
      await wishlistApi.remove(productId)
      setWishlist((prev) => prev.filter((p) => p.id !== productId))
      toast.success('Removed from wishlist')
    } catch {
      toast.error('Failed to remove item')
    }
  }

  const moveToCart = (product: Product) => {
    addItem(product)
    toast.success(`${product.name} added to bag`)
  }

  return (
    <div className="min-h-screen bg-obsidian pt-24 pb-16">
      <div className="container-luxury">
        <div className="mb-8 flex items-center gap-4">
          <Link href="/account" className="text-gold-400 hover:text-gold-300 text-sm">← Account</Link>
          <h1 className="text-3xl font-playfair text-cream">Wishlist</h1>
          {wishlist.length > 0 && (
            <span className="text-obsidian-400 text-sm">({wishlist.length} items)</span>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="aspect-[3/4] bg-obsidian-800 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : wishlist.length === 0 ? (
          <div className="text-center py-20">
            <svg className="w-16 h-16 text-obsidian-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <p className="text-obsidian-300 mb-6">Your wishlist is empty.</p>
            <Link href="/products" className="btn-gold px-8 py-3">Discover Fragrances</Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {wishlist.map((product) => {
              const brandName = (product as any).brand?.name || ''
              const imageUrl = getProductImage(product.images?.[0]?.url)
              return (
                <div key={product.id} className="group relative bg-obsidian-800 rounded-lg overflow-hidden border border-obsidian-700 hover:border-gold-600 transition-colors">
                  <Link href={`/products/${product.slug}`}>
                    <div className="relative aspect-square overflow-hidden bg-obsidian-900">
                      <Image
                        src={imageUrl}
                        alt={`${brandName} ${product.name}`}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    </div>
                    <div className="p-4">
                      {brandName && <p className="text-gold-400 text-xs uppercase tracking-wider mb-1">{brandName}</p>}
                      <p className="text-cream text-sm font-medium line-clamp-2">{product.name}</p>
                      <p className="text-cream font-semibold mt-2">{formatPrice(product.website_price)}</p>
                    </div>
                  </Link>
                  <div className="px-4 pb-4 space-y-2">
                    <button
                      onClick={() => moveToCart(product)}
                      className="w-full btn-gold py-2 text-sm"
                    >
                      Add to Bag
                    </button>
                    <button
                      onClick={() => removeFromWishlist(product.id)}
                      className="w-full text-obsidian-400 hover:text-red-400 text-xs py-1 transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
