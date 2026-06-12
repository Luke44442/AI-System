"use client";
/**
 * Premium product gallery: main stage with hover zoom, thumbnail rail,
 * and a fullscreen viewer. Falls back to the branded placeholder when a
 * product has no real photography — never a fake image.
 */
import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { XMarkIcon, ChevronLeftIcon, ChevronRightIcon, MagnifyingGlassPlusIcon } from "@heroicons/react/24/outline";
import { cn, PRODUCT_PLACEHOLDER } from "@/lib/utils";

interface ImageGalleryProps {
  images: { url: string; alt?: string }[];
  productName: string;
}

export default function ImageGallery({ images, productName }: ImageGalleryProps) {
  const urls = images.filter((i) => i.url && (i.url.startsWith("http") || i.url.startsWith("/")));
  const gallery = urls.length > 0 ? urls : [{ url: PRODUCT_PLACEHOLDER, alt: "Image coming soon" }];

  const [active, setActive] = useState(0);
  const [zoom, setZoom] = useState(false);
  const [origin, setOrigin] = useState("50% 50%");
  const [fullscreen, setFullscreen] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const prev = useCallback(() => setActive((a) => (a - 1 + gallery.length) % gallery.length), [gallery.length]);
  const next = useCallback(() => setActive((a) => (a + 1) % gallery.length), [gallery.length]);

  useEffect(() => {
    if (!fullscreen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setFullscreen(false);
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [fullscreen, prev, next]);

  return (
    <div className="space-y-3">
      {/* Main stage */}
      <div
        className="relative aspect-square surface overflow-hidden cursor-zoom-in"
        onMouseEnter={() => setZoom(true)}
        onMouseLeave={() => setZoom(false)}
        onMouseMove={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          setOrigin(`${((e.clientX - r.left) / r.width) * 100}% ${((e.clientY - r.top) / r.height) * 100}%`);
        }}
        onClick={() => setFullscreen(true)}
      >
        {!loaded && <div className="absolute inset-0 skeleton" />}
        <Image
          key={gallery[active].url}
          src={gallery[active].url}
          alt={gallery[active].alt || productName}
          fill
          priority
          sizes="(max-width: 1024px) 100vw, 50vw"
          onLoad={() => setLoaded(true)}
          className={cn(
            "object-cover transition-transform duration-300",
            zoom ? "scale-150" : "scale-100",
            loaded ? "opacity-100" : "opacity-0"
          )}
          style={{ transformOrigin: origin }}
        />
        <span className="absolute bottom-3 right-3 p-2 bg-obsidian/60 backdrop-blur-sm rounded-full opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          <MagnifyingGlassPlusIcon className="w-4 h-4 text-cream" />
        </span>
        {gallery.length > 1 && (
          <span className="absolute bottom-3 left-3 px-2 py-1 bg-obsidian/60 backdrop-blur-sm text-[11px] text-cream/80 tabular-nums">
            {active + 1} / {gallery.length}
          </span>
        )}
      </div>

      {/* Thumbnail rail */}
      {gallery.length > 1 && (
        <div className="grid grid-cols-5 gap-2">
          {gallery.slice(0, 5).map((img, i) => (
            <button
              key={i}
              onClick={() => { setLoaded(false); setActive(i); }}
              className={cn(
                "relative aspect-square overflow-hidden border transition-colors",
                i === active ? "border-gold-500" : "border-white/10 hover:border-white/30"
              )}
            >
              <Image src={img.url} alt={`${productName} ${i + 1}`} fill sizes="120px" className="object-cover" />
            </button>
          ))}
        </div>
      )}

      {/* Fullscreen viewer */}
      {fullscreen && (
        <div className="fixed inset-0 z-[100] bg-obsidian/97 backdrop-blur flex items-center justify-center" onClick={() => setFullscreen(false)}>
          <button className="absolute top-5 right-5 p-2 text-cream/70 hover:text-cream" aria-label="Close">
            <XMarkIcon className="w-7 h-7" />
          </button>
          {gallery.length > 1 && (
            <>
              <button onClick={(e) => { e.stopPropagation(); prev(); }} className="absolute left-4 p-3 text-cream/60 hover:text-cream" aria-label="Previous image">
                <ChevronLeftIcon className="w-8 h-8" />
              </button>
              <button onClick={(e) => { e.stopPropagation(); next(); }} className="absolute right-4 p-3 text-cream/60 hover:text-cream" aria-label="Next image">
                <ChevronRightIcon className="w-8 h-8" />
              </button>
            </>
          )}
          <div className="relative w-[88vw] h-[88vh]" onClick={(e) => e.stopPropagation()}>
            <Image src={gallery[active].url} alt={productName} fill sizes="90vw" className="object-contain" />
          </div>
        </div>
      )}
    </div>
  );
}
