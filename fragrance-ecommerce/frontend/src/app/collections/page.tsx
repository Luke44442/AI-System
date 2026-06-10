import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { collectionsApi } from "@/lib/api";

export const metadata: Metadata = {
  title: "Collections | Aurevia",
  description: "Explore our curated fragrance collections.",
};

export const revalidate = 3600;

export default async function CollectionsPage() {
  let collections = [];
  try {
    collections = await collectionsApi.list();
  } catch {}

  return (
    <div className="pt-20">
      <div className="bg-cream-50 py-12 text-center">
        <p className="section-subtitle text-gold-600 mb-3">Curated</p>
        <h1 className="section-title">Collections</h1>
      </div>
      <div className="container-luxury py-16">
        {collections.length === 0 ? (
          <p className="text-center text-gray-400 py-20">Collections coming soon</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {collections.map((col: any) => (
              <Link key={col.id} href={`/collections/${col.slug}`} className="group block">
                <div className="relative aspect-[4/3] overflow-hidden bg-obsidian mb-4">
                  {col.image_url ? (
                    <Image
                      src={col.image_url}
                      alt={col.name}
                      fill
                      className="object-cover opacity-70 group-hover:opacity-50 group-hover:scale-105 transition-all duration-700"
                    />
                  ) : (
                    <div className="absolute inset-0 bg-gradient-to-br from-gold-900 to-obsidian" />
                  )}
                  <div className="absolute inset-0 flex items-end p-6">
                    <div className="text-white">
                      <p className="font-serif text-2xl">{col.name}</p>
                      {col.description && (
                        <p className="text-xs text-gray-300 mt-2 line-clamp-2">{col.description}</p>
                      )}
                    </div>
                  </div>
                </div>
                <p className="text-xs tracking-widest uppercase text-gold-600 group-hover:text-gold-700 transition-colors">
                  Explore Collection →
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
