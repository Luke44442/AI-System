'use client'

import { useState } from 'react'
import toast from 'react-hot-toast'

export default function NewsletterForm() {
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return
    setSubmitting(true)
    try {
      const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const res = await fetch(`${API}/email/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, source: 'homepage' }),
      })
      if (res.ok) {
        setDone(true)
        toast.success('You\'re on the list!')
      } else {
        toast.error('Something went wrong. Please try again.')
      }
    } catch {
      toast.error('Could not subscribe. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (done) {
    return (
      <p className="text-gold-400 text-sm py-3">
        Welcome to the inner circle. Watch your inbox.
      </p>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Your email address"
        required
        className="flex-1 bg-transparent border-b border-gray-600 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
      />
      <button
        type="submit"
        disabled={submitting}
        className="btn-gold whitespace-nowrap text-xs disabled:opacity-60"
      >
        {submitting ? 'Subscribing...' : 'Subscribe'}
      </button>
    </form>
  )
}
