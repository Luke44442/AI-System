"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth";
import { systemApi } from "@/lib/api";
import {
  ChartBarIcon,
  ShoppingBagIcon,
  TagIcon,
  UsersIcon,
  EnvelopeIcon,
  CubeIcon,
  ArrowLeftIcon,
  GlobeAltIcon,
  TruckIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

const NAV = [
  { href: "/admin/analytics", label: "Overview", icon: ChartBarIcon },
  { href: "/admin/orders", label: "Orders", icon: ShoppingBagIcon },
  { href: "/admin/products", label: "Products", icon: CubeIcon },
  { href: "/admin/marketplace", label: "Marketplace Sync", icon: GlobeAltIcon },
  { href: "/admin/supplier-queue", label: "Supplier Queue", icon: TruckIcon },
  { href: "/admin/system", label: "Failures", icon: ExclamationTriangleIcon },
  { href: "/admin/pricing", label: "Pricing Alerts", icon: TagIcon },
  { href: "/admin/customers", label: "Customers", icon: UsersIcon },
  { href: "/admin/email", label: "Email", icon: EnvelopeIcon },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { customer, token } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const [failureCount, setFailureCount] = useState(0);

  useEffect(() => {
    if (!token) { router.replace("/auth/login"); return; }
    if (customer && !customer.is_admin) { router.replace("/"); }
  }, [customer, token, router]);

  // Live failure badge: human-action backlog shown on every admin page.
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const f = await systemApi.failures();
        if (!cancelled) {
          const c = f.counts;
          setFailureCount(
            c.failed_supplier_orders + c.supplier_queue_backlog +
            c.dead_letter_listings + c.orphaned_paid_orders
          );
        }
      } catch { /* dashboard endpoint down — badge just stays stale */ }
    };
    poll();
    const t = setInterval(poll, 60_000);
    return () => { cancelled = true; clearInterval(t); };
  }, [token]);

  if (!token || (customer && !customer.is_admin)) return null;

  return (
    <div className="min-h-screen bg-[#0f0f0f] flex">
      {/* Sidebar */}
      <aside className="w-56 bg-[#0A0A0A] border-r border-[#1a1a1a] flex flex-col">
        <div className="px-6 py-5 border-b border-[#1a1a1a]">
          <Link href="/" className="flex items-center gap-2 text-[#C9A84C]">
            <ArrowLeftIcon className="w-4 h-4" />
            <span className="font-serif text-lg tracking-widest">AUREVIA</span>
          </Link>
          <p className="text-[10px] text-gray-500 mt-1 tracking-widest uppercase">Admin Console</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            const showBadge = href === "/admin/system" && failureCount > 0;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors ${
                  active
                    ? "bg-[#C9A84C]/10 text-[#C9A84C]"
                    : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="flex-1">{label}</span>
                {showBadge && (
                  <span className="bg-red-500/20 text-red-400 text-[10px] px-1.5 py-0.5 rounded-full border border-red-500/30">
                    {failureCount}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="px-6 py-4 border-t border-[#1a1a1a]">
          <div className="flex items-center gap-2 mb-2">
            <span className={`w-2 h-2 rounded-full ${failureCount === 0 ? "bg-emerald-400" : "bg-red-500 animate-pulse"}`} />
            <span className="text-[10px] uppercase tracking-widest text-gray-500">
              {failureCount === 0 ? "System healthy" : `${failureCount} need attention`}
            </span>
          </div>
          <p className="text-[11px] text-gray-600 truncate">{customer?.email}</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
