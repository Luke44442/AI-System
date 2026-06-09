import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import CartDrawer from "@/components/cart/CartDrawer";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Scentara — Luxury Fragrances",
    template: "%s | Scentara",
  },
  description: "Authentic luxury fragrances from the world's finest houses. Shop Chanel, Dior, Tom Ford, and more.",
  keywords: ["luxury perfume", "designer fragrance", "eau de parfum", "authentic perfume"],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://scentara.com",
    siteName: "Scentara",
    title: "Scentara — Luxury Fragrances",
    description: "Authentic luxury fragrances delivered worldwide.",
  },
  twitter: {
    card: "summary_large_image",
    site: "@scentara",
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
        <main className="min-h-screen">{children}</main>
        <Footer />
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
