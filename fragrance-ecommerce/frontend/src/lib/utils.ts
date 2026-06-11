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

export const PRODUCT_PLACEHOLDER = "/placeholder-product.svg";

function isUsableImage(url?: string): boolean {
  // Absolute CDN URLs or root-relative paths served from public/.
  return Boolean(url && (url.startsWith("http") || url.startsWith("/")));
}

export function hasRealImage(product: { images?: { url: string }[] }, index = 0): boolean {
  return isUsableImage(product.images?.[index]?.url);
}

export function getProductImage(product: { images?: { url: string }[] }, index = 0): string {
  const img = product.images?.[index]?.url;
  if (isUsableImage(img)) return img as string;
  // No real image → branded silhouette placeholder. Never fake a product
  // photo with stock imagery: it destroys trust at checkout.
  return PRODUCT_PLACEHOLDER;
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
