"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, customer } = useAuthStore();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [newsletter, setNewsletter] = useState(true);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (customer) router.replace("/account");
  }, [customer, router]);

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    if (!firstName.trim()) errors.firstName = "First name is required.";
    if (!lastName.trim()) errors.lastName = "Last name is required.";
    if (!email.trim()) errors.email = "Email address is required.";
    if (password.length < 8) errors.password = "Password must be at least 8 characters.";
    if (password !== confirmPassword) errors.confirmPassword = "Passwords do not match.";
    if (!acceptedTerms) errors.terms = "You must accept the terms to continue.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!validate()) return;

    try {
      await register(email, password, firstName, lastName);
      router.push("/account");
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        "Registration failed. Please try again.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
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
              "radial-gradient(circle at 40% 60%, rgb(201 168 76 / 0.4) 0%, transparent 60%)",
          }}
        />
        <div className="relative z-10">
          <p className="text-xs tracking-[0.4em] uppercase text-gold-500 mb-4">
            Aurevia
          </p>
          <h2 className="font-serif text-4xl xl:text-5xl text-cream leading-tight mb-6">
            Begin Your
            <br />
            <em>Olfactory Journey</em>
          </h2>
          <p className="text-gray-400 text-sm leading-relaxed max-w-xs">
            Create your account for early access to new arrivals, exclusive
            member pricing, and curated recommendations.
          </p>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-16 bg-cream overflow-y-auto">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-10">
            <Link href="/" className="font-serif text-2xl text-obsidian tracking-widest">
              AUREVIA
            </Link>
          </div>

          <div className="mb-10">
            <p className="text-xs tracking-[0.3em] uppercase text-gold-600 mb-2">
              Create Account
            </p>
            <h1 className="font-serif text-3xl text-obsidian">Join Aurevia</h1>
          </div>

          {error && (
            <div className="mb-6 px-4 py-3 bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-7">
            {/* Name row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs tracking-widest uppercase text-gray-500 mb-2">
                  First Name
                </label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Jane"
                  autoComplete="given-name"
                  className="input-luxury"
                />
                {fieldErrors.firstName && (
                  <p className="text-red-500 text-xs mt-1">{fieldErrors.firstName}</p>
                )}
              </div>
              <div>
                <label className="block text-xs tracking-widest uppercase text-gray-500 mb-2">
                  Last Name
                </label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Smith"
                  autoComplete="family-name"
                  className="input-luxury"
                />
                {fieldErrors.lastName && (
                  <p className="text-red-500 text-xs mt-1">{fieldErrors.lastName}</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-xs tracking-widest uppercase text-gray-500 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                autoComplete="email"
                className="input-luxury"
              />
              {fieldErrors.email && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-xs tracking-widest uppercase text-gray-500 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                autoComplete="new-password"
                className="input-luxury"
              />
              {fieldErrors.password && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.password}</p>
              )}
            </div>

            <div>
              <label className="block text-xs tracking-widest uppercase text-gray-500 mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                autoComplete="new-password"
                className="input-luxury"
              />
              {fieldErrors.confirmPassword && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.confirmPassword}</p>
              )}
            </div>

            {/* Checkboxes */}
            <div className="space-y-4 pt-2">
              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={newsletter}
                  onChange={(e) => setNewsletter(e.target.checked)}
                  className="mt-0.5 w-4 h-4 accent-gold-500 cursor-pointer"
                />
                <span className="text-sm text-gray-600 leading-snug">
                  Receive curated newsletters with new arrivals, exclusive offers,
                  and fragrance editorials.
                </span>
              </label>

              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={acceptedTerms}
                  onChange={(e) => setAcceptedTerms(e.target.checked)}
                  className="mt-0.5 w-4 h-4 accent-gold-500 cursor-pointer"
                />
                <span className="text-sm text-gray-600 leading-snug">
                  I agree to Aurevia's{" "}
                  <Link
                    href="/terms"
                    className="text-obsidian underline underline-offset-2 hover:text-gold-600 transition-colors"
                  >
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link
                    href="/privacy"
                    className="text-obsidian underline underline-offset-2 hover:text-gold-600 transition-colors"
                  >
                    Privacy Policy
                  </Link>
                  .
                </span>
              </label>
              {fieldErrors.terms && (
                <p className="text-red-500 text-xs">{fieldErrors.terms}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full flex items-center justify-center gap-3 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Creating Account...
                </>
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          <div className="mt-10 pt-8 border-t border-gray-200 text-center">
            <p className="text-sm text-gray-500">
              Already have an account?{" "}
              <Link
                href="/auth/login"
                className="text-obsidian font-medium underline underline-offset-2 hover:text-gold-600 transition-colors"
              >
                Sign in
              </Link>
            </p>
          </div>

          <div className="mt-8 text-center">
            <Link
              href="/"
              className="text-xs tracking-widest uppercase text-gray-400 hover:text-obsidian transition-colors"
            >
              ← Back to Aurevia
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
