import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import MobileNav from "@/components/layout/MobileNav";
import CartDrawer from "@/components/cart/CartDrawer";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Aurevia — Luxury Fragrances, Sneakers, Streetwear & More",
    template: "%s | Aurevia",
  },
  description: "Aurevia is a luxury multi-category marketplace. Shop authentic fragrances, sneakers, streetwear, designer clothing, bags, watches, and accessories.",
  keywords: ["luxury fragrances", "designer sneakers", "streetwear", "designer clothing", "luxury bags", "watches", "authentic designer"],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://aurevia.com",
    siteName: "Aurevia",
    title: "Aurevia — Luxury Multi-Category Marketplace",
    description: "Authentic luxury fragrances, sneakers, streetwear, bags, and more — delivered worldwide.",
  },
  twitter: {
    card: "summary_large_image",
    site: "@aurevia",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <Navbar />
        {/* pb leaves room for the mobile bottom nav */}
        <main className="min-h-screen pb-16 lg:pb-0">{children}</main>
        <Footer />
        <MobileNav />
        <CartDrawer />
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: { background: "#0A0A0A", color: "#fff", fontSize: "13px" },
            success: { iconTheme: { primary: "#C9A84C", secondary: "#fff" } },
          }}
        />
      </body>
    </html>
  );
}
