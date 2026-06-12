"use client";
/** Bottom navigation for mobile — hidden on desktop and inside the admin. */
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  HomeIcon, Squares2X2Icon, MagnifyingGlassIcon, HeartIcon, UserIcon,
} from "@heroicons/react/24/outline";
import {
  HomeIcon as HomeSolid, Squares2X2Icon as GridSolid,
  MagnifyingGlassIcon as SearchSolid, HeartIcon as HeartSolid, UserIcon as UserSolid,
} from "@heroicons/react/24/solid";
import { useAuthStore } from "@/stores/auth";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/", label: "Home", icon: HomeIcon, active: HomeSolid, exact: true },
  { href: "/products", label: "Shop", icon: Squares2X2Icon, active: GridSolid },
  { href: "/search", label: "Search", icon: MagnifyingGlassIcon, active: SearchSolid },
  { href: "/account/wishlist", label: "Saved", icon: HeartIcon, active: HeartSolid },
  { href: "/account", label: "Account", icon: UserIcon, active: UserSolid },
];

export default function MobileNav() {
  const pathname = usePathname();
  const { customer } = useAuthStore();

  if (pathname.startsWith("/admin")) return null;

  return (
    <nav
      className="lg:hidden fixed bottom-0 inset-x-0 z-50 bg-obsidian/95 backdrop-blur-md border-t border-white/[0.08] pb-[env(safe-area-inset-bottom)]"
      aria-label="Mobile navigation"
    >
      <div className="grid grid-cols-5">
        {TABS.map(({ href, label, icon: Icon, active: ActiveIcon, exact }) => {
          const isActive = exact ? pathname === href : pathname.startsWith(href);
          const target = href.startsWith("/account") && !customer ? "/auth/login" : href;
          const Render = isActive ? ActiveIcon : Icon;
          return (
            <Link
              key={href}
              href={target}
              className={cn(
                "flex flex-col items-center gap-1 py-2.5 transition-colors",
                isActive ? "text-gold-500" : "text-white/45 hover:text-white/80"
              )}
            >
              <Render className="w-5 h-5" />
              <span className="text-[9px] tracking-[0.15em] uppercase">{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
