'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/stores/auth'
import { ordersApi } from '@/lib/api'
import { formatPrice, formatDate } from '@/lib/utils'

const STATUS_STYLES: Record<string, string> = {
  pending_payment: 'bg-yellow-900/30 text-yellow-300',
  pending: 'bg-yellow-900/30 text-yellow-300',
  confirmed: 'bg-blue-900/30 text-blue-300',
  shipped: 'bg-indigo-900/30 text-indigo-300',
  delivered: 'bg-green-900/30 text-green-300',
  cancelled: 'bg-red-900/30 text-red-300',
}

export default function OrderDetailPage() {
  const params = useParams()
  const router = useRouter()
  const user = useAuthStore((s) => s.user)
  const [order, setOrder] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { router.push('/auth/login'); return }
    if (params.id) fetchOrder(params.id as string)
  }, [user, params.id])

  const fetchOrder = async (id: string) => {
    setLoading(true)
    try {
      const res = await ordersApi.get(id)
      setOrder(res)
    } catch {
      setOrder(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-obsidian pt-24 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-gold-400 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-obsidian pt-24 flex items-center justify-center">
        <div className="text-center">
          <p className="text-obsidian-300 mb-4">Order not found.</p>
          <Link href="/account/orders" className="btn-gold px-6 py-2">Back to Orders</Link>
        </div>
      </div>
    )
  }

  const addr = order.shipping_address || {}

  return (
    <div className="min-h-screen bg-obsidian pt-24 pb-16">
      <div className="container-luxury max-w-4xl">
        <div className="mb-8 flex items-center gap-4 flex-wrap">
          <Link href="/account/orders" className="text-gold-400 hover:text-gold-300 text-sm">← Orders</Link>
          <h1 className="text-2xl font-playfair text-cream">Order {order.order_number}</h1>
          <span className={`px-3 py-1 rounded-full text-xs ${STATUS_STYLES[order.status] || 'bg-obsidian-700 text-obsidian-300'}`}>
            {order.status?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Items */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-obsidian-800 rounded-lg p-6">
              <h3 className="text-gold-400 font-semibold mb-4 uppercase tracking-wider text-sm">Items</h3>
              <div className="space-y-4">
                {(order.items || []).map((item: any) => (
                  <div key={item.id} className="flex justify-between items-start">
                    <div>
                      <p className="text-cream">{item.name}</p>
                      <p className="text-obsidian-400 text-sm">SKU: {item.sku} · Qty: {item.quantity}</p>
                    </div>
                    <p className="text-cream">{formatPrice(item.total)}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Tracking */}
            {order.tracking_number && (
              <div className="bg-obsidian-800 rounded-lg p-6">
                <h3 className="text-gold-400 font-semibold mb-3 uppercase tracking-wider text-sm">Tracking</h3>
                <p className="text-cream font-mono">{order.tracking_number}</p>
                {order.carrier && <p className="text-obsidian-400 text-sm mt-1">Carrier: {order.carrier}</p>}
                {order.tracking_url && (
                  <a href={order.tracking_url} target="_blank" rel="noopener noreferrer" className="text-gold-400 hover:text-gold-300 text-sm mt-2 inline-block">
                    Track Package →
                  </a>
                )}
              </div>
            )}
          </div>

          {/* Summary + Address */}
          <div className="space-y-6">
            <div className="bg-obsidian-800 rounded-lg p-6">
              <h3 className="text-gold-400 font-semibold mb-4 uppercase tracking-wider text-sm">Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-obsidian-300">
                  <span>Subtotal</span><span>{formatPrice(order.subtotal)}</span>
                </div>
                <div className="flex justify-between text-obsidian-300">
                  <span>Shipping</span><span>{formatPrice(order.shipping_amount)}</span>
                </div>
                {order.discount_amount > 0 && (
                  <div className="flex justify-between text-green-400">
                    <span>Discount</span><span>-{formatPrice(order.discount_amount)}</span>
                  </div>
                )}
                <div className="flex justify-between text-cream font-semibold border-t border-obsidian-700 pt-2 mt-2">
                  <span>Total</span><span className="text-gold-400">{formatPrice(order.total)}</span>
                </div>
              </div>
              <p className="text-obsidian-400 text-xs mt-3">Ordered on {formatDate(order.created_at)}</p>
            </div>

            {addr.address_line1 && (
              <div className="bg-obsidian-800 rounded-lg p-6">
                <h3 className="text-gold-400 font-semibold mb-3 uppercase tracking-wider text-sm">Ships To</h3>
                <div className="text-sm text-obsidian-300 space-y-1">
                  <p className="text-cream">{addr.first_name} {addr.last_name}</p>
                  <p>{addr.address_line1}</p>
                  {addr.address_line2 && <p>{addr.address_line2}</p>}
                  <p>{addr.city}, {addr.state} {addr.postal_code}</p>
                  <p>{addr.country}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
