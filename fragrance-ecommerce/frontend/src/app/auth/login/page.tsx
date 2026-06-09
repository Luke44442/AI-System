"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, customer } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (customer) router.replace("/account");
  }, [customer, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      router.push("/account");
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        "Invalid email or password. Please try again.";
      setError(msg);
    }
  };

  return (
    <div className="min-h-screen bg-obsidian flex items-stretch">
      {/* Left decorative panel */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden items-end p-16">
        <div className="absolute inset-0 bg-gradient-to-br from-[#1a1408] via-obsidian to-[#0d0d0d]" />
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle at 60% 40%, rgb(201 168 76 / 0.4) 0%, transparent 60%)",
          }}
        />
        <div className="relative z-10">
          <p className="text-xs tracking-[0.4em] uppercase text-gold-500 mb-4">
            Scentara
          </p>
          <h2 className="font-serif text-4xl xl:text-5xl text-cream leading-tight mb-6">
            The World's Finest
            <br />
            <em>Fragrances</em>
          </h2>
          <p className="text-gray-400 text-sm leading-relaxed max-w-xs">
            Discover an exclusive selection of luxury perfumes from the world's
            most prestigious fragrance houses.
          </p>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-16 bg-cream">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-10">
            <Link href="/" className="font-serif text-2xl text-obsidian tracking-widest">
              SCENTARA
            </Link>
          </div>

          <div className="mb-10">
            <p className="text-xs tracking-[0.3em] uppercase text-gold-600 mb-2">
              Welcome Back
            </p>
            <h1 className="font-serif text-3xl text-obsidian">Sign In</h1>
          </div>

          {error && (
            <div className="mb-6 px-4 py-3 bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-8">
            <div>
              <label className="block text-xs tracking-widest uppercase text-gray-500 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="your@email.com"
                className="input-luxury"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs tracking-widest uppercase text-gray-500">
                  Password
                </label>
                <Link
                  href="/auth/forgot-password"
                  className="text-xs text-gold-600 hover:text-gold-700 transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="••••••••"
                className="input-luxury"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full flex items-center justify-center gap-3 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Signing In...
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          <div className="mt-10 pt-8 border-t border-gray-200 text-center">
            <p className="text-sm text-gray-500">
              New to Scentara?{" "}
              <Link
                href="/auth/register"
                className="text-obsidian font-medium underline underline-offset-2 hover:text-gold-600 transition-colors"
              >
                Create an account
              </Link>
            </p>
          </div>

          <div className="mt-8 text-center">
            <Link
              href="/"
              className="text-xs tracking-widest uppercase text-gray-400 hover:text-obsidian transition-colors"
            >
              ← Back to Scentara
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
