'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { loadStripe } from '@stripe/stripe-js'
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js'
import { useCartStore } from '@/stores/cart'
import { formatPrice } from '@/lib/utils'
import { api, checkoutApi, type OrderQuote } from '@/lib/api'
import toast from 'react-hot-toast'
import Link from 'next/link'

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '')

interface ShippingForm {
  first_name: string
  last_name: string
  email: string
  phone: string
  address_line1: string
  address_line2: string
  city: string
  state: string
  postal_code: string
  country: string
}

function CheckoutForm({
  clientSecret,
  orderId,
  orderNumber,
  total,
}: {
  clientSecret: string
  orderId: string
  orderNumber: string
  total: number
}) {
  const stripe = useStripe()
  const elements = useElements()
  const [processing, setProcessing] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!stripe || !elements) return

    setProcessing(true)
    setErrorMessage(null)

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/checkout/success?order_id=${orderId}&order_number=${orderNumber}`,
      },
    })

    if (error) {
      setErrorMessage(error.message || 'Payment failed. Please try again.')
      setProcessing(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-obsidian-800 rounded-lg p-6">
        <h3 className="text-gold-400 font-semibold mb-4 uppercase tracking-wider text-sm">
          Payment Details
        </h3>
        <PaymentElement options={{ layout: 'tabs' }} />
      </div>

      {errorMessage && (
        <div className="bg-red-900/30 border border-red-600 rounded-lg p-4 text-red-300 text-sm">
          {errorMessage}
        </div>
      )}

      <button
        type="submit"
        disabled={!stripe || !elements || processing}
        className="w-full btn-gold py-4 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {processing ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Processing Payment...
          </span>
        ) : (
          `Pay ${formatPrice(total)}`
        )}
      </button>

      <p className="text-center text-obsidian-300 text-xs">
        Secured by Stripe · SSL Encrypted · Order #{orderNumber}
      </p>
    </form>
  )
}

export default function CheckoutPage() {
  const router = useRouter()
  const items = useCartStore((s) => s.items)
  const totalFn = useCartStore((s) => s.total)
  const [clientSecret, setClientSecret] = useState<string | null>(null)
  const [orderId, setOrderId] = useState<string | null>(null)
  const [orderNumber, setOrderNumber] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [shippingStep, setShippingStep] = useState(true)
  const [shipping, setShipping] = useState<ShippingForm>({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'US',
  })

  const [discountCode, setDiscountCode] = useState('')
  const [appliedCode, setAppliedCode] = useState('')
  const [quote, setQuote] = useState<OrderQuote | null>(null)

  const cartTotal = totalFn()
  const shippingCost = cartTotal < 150 ? 9.99 : 0
  // Prefer the server quote (includes tax + validated discount) once available.
  const orderTotal = quote?.total ?? cartTotal + shippingCost

  useEffect(() => {
    if (items.length === 0) router.push('/products')
  }, [items, router])

  const lineItems = useCallback(
    () => items.map((item) => ({ product_id: item.product.id, quantity: item.quantity })),
    [items]
  )

  // Refresh the price quote (tax + discount) when the destination or code changes.
  const refreshQuote = useCallback(async (code?: string) => {
    if (items.length === 0) return
    try {
      const q = await checkoutApi.quote(
        lineItems(),
        { state: shipping.state, country: shipping.country, postal_code: shipping.postal_code },
        code ?? appliedCode ?? undefined,
      )
      setQuote(q)
      if (code !== undefined) {
        if (q.discount_valid) toast.success('Discount applied')
        else if (q.discount_message) toast.error(q.discount_message)
      }
    } catch {
      /* keep local estimate */
    }
  }, [items, lineItems, shipping.state, shipping.country, shipping.postal_code, appliedCode])

  useEffect(() => { refreshQuote() }, [refreshQuote])

  const applyDiscount = async () => {
    const code = discountCode.trim()
    if (!code) return
    setAppliedCode(code)
    await refreshQuote(code)
  }

  const handleShippingSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      setLoading(true)
      try {
        const payload = {
          items: items.map((item) => ({
            product_id: item.product.id,
            quantity: item.quantity,
          })),
          customer_email: shipping.email,
          discount_code: appliedCode || undefined,
          shipping_address: {
            first_name: shipping.first_name,
            last_name: shipping.last_name,
            email: shipping.email,
            phone: shipping.phone,
            address_line1: shipping.address_line1,
            address_line2: shipping.address_line2,
            city: shipping.city,
            state: shipping.state,
            postal_code: shipping.postal_code,
            country: shipping.country,
          },
        }
        const response = await api.post('/checkout/create-payment-intent', payload)
        setClientSecret(response.data.client_secret)
        setOrderId(response.data.order_id)
        setOrderNumber(response.data.order_number)
        setShippingStep(false)
      } catch (err: any) {
        toast.error(err.response?.data?.detail || 'Failed to initialize payment. Please try again.')
      } finally {
        setLoading(false)
      }
    },
    [items, shipping, appliedCode]
  )

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-obsidian flex items-center justify-center">
        <p className="text-obsidian-300">Redirecting...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-obsidian py-12">
      <div className="container-luxury">
        <div className="mb-8">
          <Link href="/products" className="text-gold-400 hover:text-gold-300 text-sm flex items-center gap-1 mb-4">
            ← Continue Shopping
          </Link>
          <h1 className="text-3xl font-playfair text-cream">Secure Checkout</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Form column */}
          <div className="lg:col-span-3 space-y-6">
            {/* Step indicator */}
            <div className="flex items-center gap-3 mb-6">
              <div className={`flex items-center gap-2 text-sm font-medium ${shippingStep ? 'text-gold-400' : 'text-obsidian-400'}`}>
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${shippingStep ? 'bg-gold-500 text-obsidian' : 'bg-obsidian-600 text-obsidian-300'}`}>1</span>
                Shipping
              </div>
              <div className="flex-1 h-px bg-obsidian-700" />
              <div className={`flex items-center gap-2 text-sm font-medium ${!shippingStep ? 'text-gold-400' : 'text-obsidian-400'}`}>
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${!shippingStep ? 'bg-gold-500 text-obsidian' : 'bg-obsidian-600 text-obsidian-300'}`}>2</span>
                Payment
              </div>
            </div>

            {shippingStep ? (
              <form onSubmit={handleShippingSubmit} className="space-y-6">
                <div className="bg-obsidian-800 rounded-lg p-6">
                  <h3 className="text-gold-400 font-semibold mb-4 uppercase tracking-wider text-sm">
                    Contact Information
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-obsidian-300 text-sm mb-1">First Name *</label>
                      <input required value={shipping.first_name} onChange={(e) => setShipping((s) => ({ ...s, first_name: e.target.value }))} className="input-luxury" placeholder="John" />
                    </div>
                    <div>
                      <label className="block text-obsidian-300 text-sm mb-1">Last Name *</label>
                      <input required value={shipping.last_name} onChange={(e) => setShipping((s) => ({ ...s, last_name: e.target.value }))} className="input-luxury" placeholder="Doe" />
                    </div>
                  </div>
                  <div className="mt-4">
                    <label className="block text-obsidian-300 text-sm mb-1">Email *</label>
                    <input required type="email" value={shipping.email} onChange={(e) => setShipping((s) => ({ ...s, email: e.target.value }))} className="input-luxury" placeholder="john@example.com" />
                  </div>
                  <div className="mt-4">
                    <label className="block text-obsidian-300 text-sm mb-1">Phone</label>
                    <input type="tel" value={shipping.phone} onChange={(e) => setShipping((s) => ({ ...s, phone: e.target.value }))} className="input-luxury" placeholder="+1 (555) 000-0000" />
                  </div>
                </div>

                <div className="bg-obsidian-800 rounded-lg p-6">
                  <h3 className="text-gold-400 font-semibold mb-4 uppercase tracking-wider text-sm">
                    Shipping Address
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-obsidian-300 text-sm mb-1">Address *</label>
                      <input required value={shipping.address_line1} onChange={(e) => setShipping((s) => ({ ...s, address_line1: e.target.value }))} className="input-luxury" placeholder="123 Main Street" />
                    </div>
                    <div>
                      <label className="block text-obsidian-300 text-sm mb-1">Apt, Suite (optional)</label>
                      <input value={shipping.address_line2} onChange={(e) => setShipping((s) => ({ ...s, address_line2: e.target.value }))} className="input-luxury" placeholder="Apt 4B" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-obsidian-300 text-sm mb-1">City *</label>
                        <input required value={shipping.city} onChange={(e) => setShipping((s) => ({ ...s, city: e.target.value }))} className="input-luxury" placeholder="New York" />
                      </div>
                      <div>
                        <label className="block text-obsidian-300 text-sm mb-1">State *</label>
                        <input required value={shipping.state} onChange={(e) => setShipping((s) => ({ ...s, state: e.target.value }))} className="input-luxury" placeholder="NY" />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-obsidian-300 text-sm mb-1">ZIP Code *</label>
                        <input required value={shipping.postal_code} onChange={(e) => setShipping((s) => ({ ...s, postal_code: e.target.value }))} className="input-luxury" placeholder="10001" />
                      </div>
                      <div>
                        <label className="block text-obsidian-300 text-sm mb-1">Country</label>
                        <select value={shipping.country} onChange={(e) => setShipping((s) => ({ ...s, country: e.target.value }))} className="input-luxury">
                          <option value="US">United States</option>
                          <option value="CA">Canada</option>
                          <option value="GB">United Kingdom</option>
                          <option value="AU">Australia</option>
                          <option value="DE">Germany</option>
                          <option value="FR">France</option>
                          <option value="IT">Italy</option>
                          <option value="JP">Japan</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                <button type="submit" disabled={loading} className="w-full btn-gold py-4 text-lg font-semibold disabled:opacity-50">
                  {loading ? 'Preparing Payment...' : 'Continue to Payment →'}
                </button>
              </form>
            ) : clientSecret ? (
              <Elements
                stripe={stripePromise}
                options={{
                  clientSecret,
                  appearance: {
                    theme: 'night',
                    variables: {
                      colorPrimary: '#C9A84C',
                      colorBackground: '#1A1A2E',
                      colorText: '#F5F0E8',
                      colorDanger: '#EF4444',
                      fontFamily: 'Inter, sans-serif',
                      borderRadius: '6px',
                    },
                  },
                }}
              >
                <div className="mb-4">
                  <button onClick={() => setShippingStep(true)} className="text-gold-400 hover:text-gold-300 text-sm flex items-center gap-1">
                    ← Edit Shipping
                  </button>
                </div>
                <div className="bg-obsidian-800 rounded-lg p-4 mb-4 text-sm">
                  <p className="text-obsidian-300">Shipping to:</p>
                  <p className="text-cream">
                    {shipping.first_name} {shipping.last_name} — {shipping.address_line1}, {shipping.city}, {shipping.state} {shipping.postal_code}
                  </p>
                </div>
                <CheckoutForm
                  clientSecret={clientSecret}
                  orderId={orderId!}
                  orderNumber={orderNumber!}
                  total={orderTotal}
                />
              </Elements>
            ) : null}
          </div>

          {/* Order summary */}
          <div className="lg:col-span-2">
            <div className="bg-obsidian-800 rounded-lg p-6 sticky top-24">
              <h3 className="text-gold-400 font-semibold mb-4 uppercase tracking-wider text-sm">
                Order Summary
              </h3>
              <div className="space-y-3 mb-4 max-h-64 overflow-y-auto pr-1">
                {items.map((item) => {
                  const price = item.variant?.website_price ?? item.product.website_price ?? 0
                  const brandName = item.product.brand?.name ? `${item.product.brand.name} ` : ''
                  return (
                    <div key={item.id} className="flex justify-between text-sm">
                      <div className="flex-1 min-w-0">
                        <p className="text-cream truncate">{brandName}{item.product.name}</p>
                        <p className="text-obsidian-400 text-xs">Qty: {item.quantity}</p>
                      </div>
                      <p className="text-cream ml-4 shrink-0">{formatPrice(price * item.quantity)}</p>
                    </div>
                  )
                })}
              </div>

              {/* Discount code */}
              <div className="border-t border-obsidian-700 pt-4">
                <div className="flex gap-2">
                  <input
                    value={discountCode}
                    onChange={(e) => setDiscountCode(e.target.value)}
                    placeholder="Discount code"
                    className="flex-1 bg-obsidian-900 border border-obsidian-700 rounded px-3 py-2 text-sm text-cream placeholder-obsidian-500 focus:outline-none focus:border-gold-500 uppercase"
                  />
                  <button onClick={applyDiscount} type="button" className="btn-outline px-4 py-2 text-xs">Apply</button>
                </div>
              </div>

              <div className="border-t border-obsidian-700 pt-4 mt-4 space-y-2">
                <div className="flex justify-between text-sm text-obsidian-300">
                  <span>Subtotal</span>
                  <span>{formatPrice(quote?.subtotal ?? cartTotal)}</span>
                </div>
                {quote && quote.discount > 0 && (
                  <div className="flex justify-between text-sm text-green-400">
                    <span>Discount{appliedCode ? ` (${appliedCode})` : ''}</span>
                    <span>−{formatPrice(quote.discount)}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm text-obsidian-300">
                  <span>Shipping</span>
                  <span>{(quote?.shipping ?? shippingCost) === 0 ? <span className="text-gold-400">FREE</span> : formatPrice(quote?.shipping ?? shippingCost)}</span>
                </div>
                <div className="flex justify-between text-sm text-obsidian-300">
                  <span>Tax{!shipping.state ? ' (est. at next step)' : ''}</span>
                  <span>{formatPrice(quote?.tax ?? 0)}</span>
                </div>
                {(quote?.subtotal ?? cartTotal) < 150 && (
                  <p className="text-xs text-obsidian-400">Add {formatPrice(150 - (quote?.subtotal ?? cartTotal))} for free shipping</p>
                )}
                <div className="flex justify-between font-semibold text-cream border-t border-obsidian-700 pt-2 mt-2">
                  <span>Total</span>
                  <span className="text-gold-400">{formatPrice(orderTotal)}</span>
                </div>
              </div>

              <div className="mt-6 space-y-2 text-xs text-obsidian-400">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-gold-500 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                  </svg>
                  256-bit SSL encryption
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-gold-500 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  30-day return guarantee
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-gold-500 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
                    <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H11a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7h4l2 5H14V7z" />
                  </svg>
                  Tracked worldwide shipping
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
