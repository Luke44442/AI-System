'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useCartStore } from '@/stores/cart'

export default function CheckoutSuccessPage() {
  const searchParams = useSearchParams()
  const orderId = searchParams.get('order_id')
  const orderNumber = searchParams.get('order_number')
  const clearCart = useCartStore((s) => s.clearCart)
  const [cleared, setCleared] = useState(false)

  useEffect(() => {
    if (!cleared) {
      clearCart()
      setCleared(true)
    }
  }, [clearCart, cleared])

  return (
    <div className="min-h-screen bg-obsidian flex items-center justify-center py-16">
      <div className="text-center max-w-md mx-auto px-6">
        <div className="w-20 h-20 bg-gold-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-10 h-10 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="text-3xl font-playfair text-cream mb-3">Thank You!</h1>
        <p className="text-obsidian-300 mb-2">Your order has been confirmed</p>
        {orderNumber && (
          <p className="text-gold-400 font-semibold text-lg mb-6">Order #{orderNumber}</p>
        )}

        <div className="bg-obsidian-800 rounded-lg p-6 mb-8 text-left space-y-3">
          <h3 className="text-cream font-semibold">What happens next?</h3>
          <div className="space-y-2 text-sm text-obsidian-300">
            <div className="flex items-start gap-2">
              <span className="text-gold-400 mt-0.5">1.</span>
              <span>You'll receive a confirmation email with your order details</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-gold-400 mt-0.5">2.</span>
              <span>Your order will be processed and dispatched within 1-3 business days</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-gold-400 mt-0.5">3.</span>
              <span>Tracking information will be emailed once shipped (est. 7-14 days delivery)</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link href="/products" className="btn-gold px-8 py-3">
            Continue Shopping
          </Link>
          {orderId && (
            <Link href={`/account/orders/${orderId}`} className="btn-outline px-8 py-3">
              View Order
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}
