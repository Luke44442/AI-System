import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(price);
}

export function formatDate(dateString: string): string {
  return new Intl.DateTimeFormat("en-US", { year: "numeric", month: "long", day: "numeric" }).format(new Date(dateString));
}

export function getProductImage(product: { images?: { url: string }[] }, index = 0): string {
  const img = product.images?.[index]?.url;
  if (img && img.startsWith("http")) return img;
  return `https://images.unsplash.com/photo-1541643600914-78b084683702?w=600&h=800&fit=crop`;
}

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen - 3) + "...";
}

export function concentrationLabel(concentration?: string): string {
  const map: Record<string, string> = {
    "eau de parfum": "EDP",
    "edp": "EDP",
    "eau de toilette": "EDT",
    "edt": "EDT",
    "parfum": "Parfum",
    "extrait de parfum": "Extrait",
    "eau de cologne": "EDC",
    "edc": "EDC",
  };
  if (!concentration) return "";
  return map[concentration.toLowerCase()] || concentration;
}
