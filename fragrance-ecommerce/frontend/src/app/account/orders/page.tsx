'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/stores/auth'
import { ordersApi } from '@/lib/api'
import { formatPrice, formatDate } from '@/lib/utils'

const STATUS_STYLES: Record<string, string> = {
  pending_payment: 'bg-yellow-900/30 text-yellow-300 border-yellow-700',
  pending: 'bg-yellow-900/30 text-yellow-300 border-yellow-700',
  confirmed: 'bg-blue-900/30 text-blue-300 border-blue-700',
  processing: 'bg-purple-900/30 text-purple-300 border-purple-700',
  shipped: 'bg-indigo-900/30 text-indigo-300 border-indigo-700',
  delivered: 'bg-green-900/30 text-green-300 border-green-700',
  cancelled: 'bg-red-900/30 text-red-300 border-red-700',
  refunded: 'bg-gray-900/30 text-gray-300 border-gray-700',
}

export default function OrdersPage() {
  const router = useRouter()
  const user = useAuthStore((s) => s.customer)
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    if (!user) { router.push('/auth/login'); return }
    fetchOrders()
  }, [user, page])

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const res = await ordersApi.myOrders({ page, page_size: 20 })
      setOrders(res.items || [])
      setTotal(res.total || 0)
    } catch {
      setOrders([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-obsidian pt-24 pb-16">
      <div className="container-luxury max-w-4xl">
        <div className="mb-8 flex items-center gap-4">
          <Link href="/account" className="text-gold-400 hover:text-gold-300 text-sm">← Account</Link>
          <h1 className="text-3xl font-playfair text-cream">Order History</h1>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="bg-obsidian-800 rounded-lg h-24 animate-pulse" />
            ))}
          </div>
        ) : orders.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-obsidian-300 mb-6">You haven't placed any orders yet.</p>
            <Link href="/products" className="btn-gold px-8 py-3">Shop Now</Link>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <Link
                key={order.id}
                href={`/account/orders/${order.id}`}
                className="block bg-obsidian-800 rounded-lg p-6 hover:bg-obsidian-700 transition-colors border border-obsidian-700 hover:border-gold-600"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-cream font-semibold">{order.order_number}</p>
                    <p className="text-obsidian-400 text-sm mt-1">{formatDate(order.created_at)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-gold-400 font-semibold text-lg">{formatPrice(order.total)}</p>
                    <span className={`inline-block mt-1 px-3 py-1 rounded-full text-xs border ${STATUS_STYLES[order.status] || STATUS_STYLES.pending}`}>
                      {order.status?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
                    </span>
                  </div>
                </div>
                {order.items?.length > 0 && (
                  <p className="text-obsidian-400 text-sm mt-3">
                    {order.items.length} item{order.items.length !== 1 ? 's' : ''}
                    {order.tracking_number && ` · Tracking: ${order.tracking_number}`}
                  </p>
                )}
              </Link>
            ))}
          </div>
        )}

        {total > 20 && (
          <div className="flex justify-center gap-3 mt-8">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="btn-outline px-4 py-2 disabled:opacity-40">
              Previous
            </button>
            <span className="text-obsidian-300 py-2">Page {page}</span>
            <button onClick={() => setPage((p) => p + 1)} disabled={orders.length < 20} className="btn-outline px-4 py-2 disabled:opacity-40">
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
