'use client'

import { Suspense, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { authApi } from '@/lib/api'
import toast from 'react-hot-toast'

function ResetPasswordForm() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token') || ''
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (password.length < 8) { toast.error('Password must be at least 8 characters'); return }
    if (password !== confirm) { toast.error('Passwords do not match'); return }
    setSubmitting(true)
    try {
      await authApi.resetPassword(token, password)
      toast.success('Password updated. Please sign in.')
      router.push('/auth/login')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Invalid or expired reset link')
    } finally {
      setSubmitting(false)
    }
  }

  if (!token) {
    return (
      <div className="bg-obsidian-800 rounded-lg p-6 text-center">
        <p className="text-cream mb-2">Invalid reset link</p>
        <Link href="/auth/forgot-password" className="btn-gold inline-block mt-4 px-6 py-2 text-sm">Request a new link</Link>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <input
        type="password" value={password} onChange={(e) => setPassword(e.target.value)}
        placeholder="New password" required
        className="w-full bg-obsidian-800 border border-obsidian-700 rounded px-4 py-3 text-cream placeholder-obsidian-500 focus:outline-none focus:border-gold-500"
      />
      <input
        type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
        placeholder="Confirm new password" required
        className="w-full bg-obsidian-800 border border-obsidian-700 rounded px-4 py-3 text-cream placeholder-obsidian-500 focus:outline-none focus:border-gold-500"
      />
      <button type="submit" disabled={submitting} className="btn-gold w-full py-3 disabled:opacity-60">
        {submitting ? 'Updating…' : 'Update password'}
      </button>
    </form>
  )
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-obsidian pt-24 pb-16 flex items-center justify-center">
      <div className="w-full max-w-md px-6">
        <div className="text-center mb-8">
          <Link href="/" className="font-serif text-3xl tracking-wider text-cream">AUREVIA</Link>
          <h1 className="text-2xl font-playfair text-cream mt-6">Choose a new password</h1>
        </div>
        <Suspense fallback={<div className="text-center text-obsidian-400">Loading…</div>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  )
}
