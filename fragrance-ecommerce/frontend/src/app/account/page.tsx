"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShoppingBagIcon,
  HeartIcon,
  UserIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/outline";
import { useAuthStore } from "@/stores/auth";
import { ordersApi } from "@/lib/api";
import { formatPrice, formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Order } from "@/types";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  confirmed: "bg-blue-100 text-blue-800",
  shipped: "bg-purple-100 text-purple-800",
  delivered: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

function OrderStatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-block text-[10px] tracking-widest uppercase px-2.5 py-1 font-medium",
        STATUS_STYLES[status.toLowerCase()] ?? "bg-gray-100 text-gray-700"
      )}
    >
      {status}
    </span>
  );
}

export default function AccountPage() {
  const router = useRouter();
  const customer = useAuthStore((s) => s.customer);
  const isLoading = useAuthStore((s) => s.isLoading);
  const logout = useAuthStore((s) => s.logout);

  const [orders, setOrders] = useState<Order[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [ordersError, setOrdersError] = useState(false);

  useEffect(() => {
    if (!isLoading && !customer) {
      router.replace("/auth/login");
    }
  }, [customer, isLoading, router]);

  useEffect(() => {
    if (!customer) return;
    setOrdersLoading(true);
    ordersApi
      .myOrders(1)
      .then((data) => setOrders(data.items.slice(0, 3)))
      .catch(() => setOrdersError(true))
      .finally(() => setOrdersLoading(false));
  }, [customer]);

  if (isLoading || !customer) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center bg-cream">
        <span className="inline-block w-8 h-8 border-2 border-gold-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const firstName = customer.first_name || customer.email.split("@")[0];
  const totalSpent = customer.total_spent ?? 0;
  const orderCount = customer.order_count ?? 0;

  return (
    <div className="min-h-screen bg-cream pt-20">
      {/* Hero header */}
      <div className="bg-obsidian py-16">
        <div className="container-luxury">
          <p className="text-xs tracking-[0.3em] uppercase text-gold-500 mb-2">
            My Account
          </p>
          <h1 className="font-serif text-3xl md:text-4xl text-cream">
            Welcome back, {firstName}
          </h1>
          <p className="text-gray-400 text-sm mt-2">{customer.email}</p>
        </div>
      </div>

      <div className="container-luxury py-12">
        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          {[
            { label: "Total Orders", value: orderCount.toString() },
            {
              label: "Total Spent",
              value: formatPrice(totalSpent),
            },
            { label: "Wishlist Items", value: "—" },
            { label: "Member Since", value: "2024" },
          ].map(({ label, value }) => (
            <div
              key={label}
              className="bg-white border border-gray-100 px-6 py-5"
            >
              <p className="text-xs tracking-widest uppercase text-gray-400 mb-1">
                {label}
              </p>
              <p className="font-serif text-2xl text-obsidian">{value}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Orders */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-serif text-xl text-obsidian">
                Recent Orders
              </h2>
              <Link
                href="/account/orders"
                className="text-xs tracking-widest uppercase text-gold-600 hover:text-gold-700 transition-colors flex items-center gap-1"
              >
                View All
                <ArrowRightIcon className="w-3 h-3" />
              </Link>
            </div>

            {ordersLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="animate-pulse bg-white border border-gray-100 p-5 h-20"
                  />
                ))}
              </div>
            ) : ordersError ? (
              <div className="bg-white border border-gray-100 p-8 text-center">
                <p className="text-sm text-gray-400">
                  Unable to load orders.
                </p>
              </div>
            ) : orders.length === 0 ? (
              <div className="bg-white border border-gray-100 p-12 text-center">
                <ShoppingBagIcon className="w-10 h-10 text-gray-200 mx-auto mb-3" />
                <p className="font-serif text-lg text-gray-400 mb-4">
                  No orders yet
                </p>
                <Link href="/products" className="btn-primary text-xs py-2.5 px-6">
                  Start Shopping
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {orders.map((order) => (
                  <Link
                    key={order.id}
                    href={`/account/orders/${order.id}`}
                    className="block bg-white border border-gray-100 p-5 hover:border-gold-300 transition-colors group"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-obsidian group-hover:text-gold-600 transition-colors">
                          Order #{order.order_number}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {order.items?.length ?? 0} item
                          {(order.items?.length ?? 0) !== 1 ? "s" : ""} ·{" "}
                          {formatDate(
                            (order as any).created_at ||
                              new Date().toISOString()
                          )}
                        </p>
                      </div>
                      <div className="text-right flex flex-col items-end gap-2">
                        <OrderStatusBadge status={order.status} />
                        <p className="text-sm font-medium text-obsidian">
                          {formatPrice(order.total)}
                        </p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Quick links sidebar */}
          <div>
            <h2 className="font-serif text-xl text-obsidian mb-6">
              Quick Links
            </h2>
            <div className="space-y-2">
              {[
                {
                  href: "/account/orders",
                  Icon: ShoppingBagIcon,
                  label: "Order History",
                  sub: "Track and manage your orders",
                },
                {
                  href: "/account/wishlist",
                  Icon: HeartIcon,
                  label: "My Wishlist",
                  sub: "Saved fragrances",
                },
                {
                  href: "/account/profile",
                  Icon: UserIcon,
                  label: "Edit Profile",
                  sub: "Update your details",
                },
              ].map(({ href, Icon, label, sub }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-4 bg-white border border-gray-100 p-4 hover:border-gold-300 transition-colors group"
                >
                  <div className="w-10 h-10 bg-cream flex items-center justify-center flex-shrink-0 group-hover:bg-gold-50 transition-colors">
                    <Icon className="w-5 h-5 text-gold-600" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-obsidian group-hover:text-gold-600 transition-colors">
                      {label}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">{sub}</p>
                  </div>
                  <ArrowRightIcon className="w-4 h-4 text-gray-300 ml-auto flex-shrink-0 group-hover:text-gold-400 transition-colors" />
                </Link>
              ))}

              <button
                onClick={() => {
                  logout();
                  router.push("/");
                }}
                className="w-full flex items-center gap-4 bg-white border border-gray-100 p-4 hover:border-red-200 transition-colors group text-left mt-4"
              >
                <div className="w-10 h-10 bg-cream flex items-center justify-center flex-shrink-0">
                  <svg
                    className="w-5 h-5 text-gray-400 group-hover:text-red-400 transition-colors"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v1"
                    />
                  </svg>
                </div>
                <span className="text-sm font-medium text-gray-500 group-hover:text-red-500 transition-colors">
                  Sign Out
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
