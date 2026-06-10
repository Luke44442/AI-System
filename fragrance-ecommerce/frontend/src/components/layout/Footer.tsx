import Link from "next/link";

const LINKS = {
  Shop: [
    { href: "/products", label: "All Fragrances" },
    { href: "/collections", label: "Collections" },
    { href: "/products?is_new_arrival=true", label: "New Arrivals" },
    { href: "/products?is_featured=true", label: "Best Sellers" },
  ],
  Help: [
    { href: "/faq", label: "FAQ" },
    { href: "/shipping", label: "Shipping Policy" },
    { href: "/returns", label: "Returns" },
    { href: "/contact", label: "Contact Us" },
  ],
  Company: [
    { href: "/about", label: "About Aurevia" },
    { href: "/authenticity", label: "Authenticity" },
    { href: "/privacy", label: "Privacy Policy" },
    { href: "/terms", label: "Terms of Service" },
  ],
};

export default function Footer() {
  return (
    <footer className="bg-obsidian text-white">
      <div className="container-luxury py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
          <div>
            <Link href="/" className="font-serif text-2xl tracking-wider text-white">
              AUREVIA
            </Link>
            <p className="mt-4 text-sm text-gray-400 leading-relaxed">
              Authentic luxury fragrances delivered worldwide. Every bottle tells a story.
            </p>
            <div className="mt-6 flex gap-4">
              {["instagram", "tiktok", "pinterest"].map((platform) => (
                <a
                  key={platform}
                  href={`https://${platform}.com/aurevia`}
                  className="text-gray-400 hover:text-gold-400 transition-colors text-xs tracking-widest uppercase"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {platform}
                </a>
              ))}
            </div>
          </div>

          {Object.entries(LINKS).map(([title, links]) => (
            <div key={title}>
              <h4 className="text-xs tracking-widest uppercase text-gold-400 mb-6">{title}</h4>
              <ul className="space-y-3">
                {links.map(({ href, label }) => (
                  <li key={href}>
                    <Link href={href} className="text-sm text-gray-400 hover:text-white transition-colors">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-8 border-t border-gray-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-500">
            &copy; {new Date().getFullYear()} Aurevia. All rights reserved.
          </p>
          <div className="flex gap-6">
            {["Visa", "Mastercard", "Amex", "PayPal"].map((method) => (
              <span key={method} className="text-xs text-gray-500">{method}</span>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
