'use client'

import { useState } from 'react'
import Link from 'next/link'
import { authApi } from '@/lib/api'
import toast from 'react-hot-toast'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return
    setSubmitting(true)
    try {
      await authApi.forgotPassword(email)
      setSent(true)
    } catch {
      toast.error('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-obsidian pt-24 pb-16 flex items-center justify-center">
      <div className="w-full max-w-md px-6">
        <div className="text-center mb-8">
          <Link href="/" className="font-serif text-3xl tracking-wider text-cream">AUREVIA</Link>
          <h1 className="text-2xl font-playfair text-cream mt-6">Reset your password</h1>
          <p className="text-obsidian-300 text-sm mt-2">We'll email you a secure reset link.</p>
        </div>

        {sent ? (
          <div className="bg-obsidian-800 rounded-lg p-6 text-center">
            <p className="text-cream mb-2">Check your inbox</p>
            <p className="text-obsidian-400 text-sm">
              If an account exists for <span className="text-gold-400">{email}</span>, a reset link is on its way.
            </p>
            <Link href="/auth/login" className="btn-gold inline-block mt-6 px-6 py-2 text-sm">Back to sign in</Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email address"
              required
              className="w-full bg-obsidian-800 border border-obsidian-700 rounded px-4 py-3 text-cream placeholder-obsidian-500 focus:outline-none focus:border-gold-500"
            />
            <button type="submit" disabled={submitting} className="btn-gold w-full py-3 disabled:opacity-60">
              {submitting ? 'Sending…' : 'Send reset link'}
            </button>
            <p className="text-center text-obsidian-400 text-sm">
              <Link href="/auth/login" className="text-gold-400 hover:text-gold-300">Back to sign in</Link>
            </p>
          </form>
        )}
      </div>
    </div>
  )
}
