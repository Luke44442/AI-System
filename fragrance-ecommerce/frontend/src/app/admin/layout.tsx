"use client";
import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth";
import {
  ChartBarIcon,
  ShoppingBagIcon,
  TagIcon,
  UsersIcon,
  EnvelopeIcon,
  CubeIcon,
  ArrowLeftIcon,
} from "@heroicons/react/24/outline";

const NAV = [
  { href: "/admin/analytics", label: "Analytics", icon: ChartBarIcon },
  { href: "/admin/orders", label: "Orders", icon: ShoppingBagIcon },
  { href: "/admin/products", label: "Products", icon: CubeIcon },
  { href: "/admin/customers", label: "Customers", icon: UsersIcon },
  { href: "/admin/pricing", label: "Pricing Alerts", icon: TagIcon },
  { href: "/admin/email", label: "Email", icon: EnvelopeIcon },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { customer, token } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!token) { router.replace("/auth/login"); return; }
    if (customer && !customer.is_admin) { router.replace("/"); }
  }, [customer, token, router]);

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
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="px-6 py-4 border-t border-[#1a1a1a]">
          <p className="text-[11px] text-gray-600 truncate">{customer?.email}</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
