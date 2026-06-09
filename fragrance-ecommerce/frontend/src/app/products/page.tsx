"use client";
import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { FunnelIcon, AdjustmentsHorizontalIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { productsApi, brandsApi, categoriesApi } from "@/lib/api";
import ProductGrid from "@/components/product/ProductGrid";
import type { Product, Brand, Category, PaginatedResponse, FilterState } from "@/types";
import { cn } from "@/lib/utils";

const CONCENTRATIONS = ["Eau de Parfum", "Eau de Toilette", "Parfum", "Eau de Cologne", "Body Spray"];
const GENDERS = [{ value: "male", label: "For Him" }, { value: "female", label: "For Her" }, { value: "unisex", label: "Unisex" }];
const SORT_OPTIONS = [
  { value: "created_at-desc", label: "Newest" },
  { value: "website_price-asc", label: "Price: Low to High" },
  { value: "website_price-desc", label: "Price: High to Low" },
  { value: "rating_avg-desc", label: "Top Rated" },
  { value: "order_count-desc", label: "Best Selling" },
];

export default function ProductsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [filterOpen, setFilterOpen] = useState(false);

  const getFilters = useCallback((): FilterState => ({
    search: searchParams.get("search") || undefined,
    brand_id: searchParams.get("brand_id") || undefined,
    category_id: searchParams.get("category_id") || undefined,
    gender: searchParams.get("gender") || undefined,
    concentration: searchParams.get("concentration") || undefined,
    min_price: searchParams.get("min_price") ? Number(searchParams.get("min_price")) : undefined,
    max_price: searchParams.get("max_price") ? Number(searchParams.get("max_price")) : undefined,
    sort_by: searchParams.get("sort_by") || "created_at",
    sort_dir: (searchParams.get("sort_dir") as "asc" | "desc") || "desc",
    page: Number(searchParams.get("page")) || 1,
  }), [searchParams]);

  useEffect(() => {
    Promise.all([brandsApi.list(), categoriesApi.list()]).then(([b, c]) => {
      setBrands(b);
      setCategories(c);
    });
  }, []);

  useEffect(() => {
    const filters = getFilters();
    setLoading(true);
    productsApi.list(filters as any).then((data: PaginatedResponse<Product>) => {
      setProducts(data.items);
      setTotal(data.total);
      setPages(data.pages);
    }).finally(() => setLoading(false));
  }, [getFilters]);

  const updateFilter = (key: string, value: string | undefined) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    params.delete("page");
    router.push(`/products?${params.toString()}`);
  };

  const filters = getFilters();
  const activeFiltersCount = [filters.brand_id, filters.category_id, filters.gender, filters.concentration, filters.min_price].filter(Boolean).length;

  return (
    <div className="pt-20">
      <div className="bg-cream-50 py-12 text-center">
        <p className="section-subtitle text-gold-600 mb-3">Discover</p>
        <h1 className="section-title">All Fragrances</h1>
        <p className="text-gray-500 text-sm mt-3">{total.toLocaleString()} fragrances available</p>
      </div>

      <div className="container-luxury py-8">
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => setFilterOpen(!filterOpen)}
            className={cn(
              "flex items-center gap-2 text-sm border px-4 py-2 transition-colors",
              filterOpen ? "bg-obsidian text-white border-obsidian" : "border-gray-300 hover:border-obsidian"
            )}
          >
            <FunnelIcon className="w-4 h-4" />
            Filters
            {activeFiltersCount > 0 && (
              <span className="bg-gold-500 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">{activeFiltersCount}</span>
            )}
          </button>

          <select
            value={`${filters.sort_by}-${filters.sort_dir}`}
            onChange={(e) => {
              const [by, dir] = e.target.value.split("-");
              const params = new URLSearchParams(searchParams.toString());
              params.set("sort_by", by);
              params.set("sort_dir", dir);
              router.push(`/products?${params.toString()}`);
            }}
            className="text-sm border border-gray-300 px-3 py-2 focus:outline-none focus:border-obsidian bg-white"
          >
            {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>

        {filterOpen && (
          <div className="border border-gray-200 p-6 mb-6 grid grid-cols-1 md:grid-cols-4 gap-6 bg-white">
            <div>
              <h4 className="text-xs tracking-widest uppercase mb-3 text-gray-500">Brand</h4>
              <select
                value={filters.brand_id || ""}
                onChange={(e) => updateFilter("brand_id", e.target.value || undefined)}
                className="w-full text-sm border border-gray-200 px-3 py-2 focus:outline-none focus:border-obsidian"
              >
                <option value="">All Brands</option>
                {brands.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>
            <div>
              <h4 className="text-xs tracking-widest uppercase mb-3 text-gray-500">Category</h4>
              <select
                value={filters.category_id || ""}
                onChange={(e) => updateFilter("category_id", e.target.value || undefined)}
                className="w-full text-sm border border-gray-200 px-3 py-2 focus:outline-none focus:border-obsidian"
              >
                <option value="">All Categories</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <h4 className="text-xs tracking-widest uppercase mb-3 text-gray-500">Gender</h4>
              <div className="flex flex-wrap gap-2">
                {GENDERS.map(({ value, label }) => (
                  <button
                    key={value}
                    onClick={() => updateFilter("gender", filters.gender === value ? undefined : value)}
                    className={cn(
                      "text-xs px-3 py-1.5 border transition-colors",
                      filters.gender === value ? "bg-obsidian text-white border-obsidian" : "border-gray-200 hover:border-obsidian"
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-xs tracking-widest uppercase mb-3 text-gray-500">Concentration</h4>
              <div className="flex flex-wrap gap-2">
                {CONCENTRATIONS.map((c) => (
                  <button
                    key={c}
                    onClick={() => updateFilter("concentration", filters.concentration === c.toLowerCase() ? undefined : c.toLowerCase())}
                    className={cn(
                      "text-xs px-3 py-1.5 border transition-colors",
                      filters.concentration === c.toLowerCase() ? "bg-obsidian text-white border-obsidian" : "border-gray-200 hover:border-obsidian"
                    )}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        <ProductGrid products={products} loading={loading} />

        {pages > 1 && (
          <div className="flex justify-center gap-2 mt-12">
            {Array.from({ length: Math.min(pages, 10) }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                onClick={() => updateFilter("page", String(p))}
                className={cn(
                  "w-10 h-10 text-sm border transition-colors",
                  filters.page === p ? "bg-obsidian text-white border-obsidian" : "border-gray-200 hover:border-obsidian"
                )}
              >
                {p}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
