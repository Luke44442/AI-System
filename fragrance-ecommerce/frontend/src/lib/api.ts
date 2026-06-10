import axios from "axios";
import type { Product, PaginatedResponse, Collection, Category, Brand, Order, Customer } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("aurevia_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("aurevia_token");
    }
    return Promise.reject(error);
  }
);

export interface ProductParams {
  page?: number;
  page_size?: number;
  search?: string;
  brand_id?: string;
  brand_slug?: string;
  category_id?: string;
  category_slug?: string;
  gender?: string;
  concentration?: string;
  is_featured?: boolean;
  is_bestseller?: boolean;
  min_price?: number;
  max_price?: number;
  /** JSON-encoded attribute filters, e.g. {"size":"10","colorway":"Panda"} */
  attributes?: string;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
}

export interface CategoryAttribute {
  key: string;
  label: string;
  data_type: "string" | "number" | "enum" | "multi_enum" | "boolean";
  options: string[];
  unit: string | null;
  is_filterable: boolean;
  is_required: boolean;
  is_variant_axis: boolean;
  sort_order: number;
}

export interface CategoryAttributeSchema {
  category: { id: string; name: string; slug: string; schema_type: string | null };
  attributes: CategoryAttribute[];
}

export const productsApi = {
  list: (params?: ProductParams) =>
    api.get<PaginatedResponse<Product>>("/products", { params }).then((r) => r.data),
  get: (slug: string) =>
    api.get<Product>(`/products/${slug}`).then((r) => r.data),
  getFeatured: () =>
    api.get<PaginatedResponse<Product>>("/products", { params: { is_featured: true, page_size: 8 } }).then((r) => r.data),
};

export const collectionsApi = {
  list: () => api.get<Collection[]>("/collections").then((r) => r.data),
  get: (slug: string) => api.get<Collection>(`/collections/${slug}`).then((r) => r.data),
};

export const categoriesApi = {
  list: () => api.get<Category[]>("/categories").then((r) => r.data),
  getAttributes: (slug: string) =>
    api.get<CategoryAttributeSchema>(`/categories/${slug}/attributes`).then((r) => r.data),
};

export const brandsApi = {
  list: () => api.get<Brand[]>("/brands").then((r) => r.data),
};

export const ordersApi = {
  create: (data: object) => api.post<Order>("/orders", data).then((r) => r.data),
  get: (id: string) => api.get<Order>(`/orders/${id}`).then((r) => r.data),
  myOrders: (params: { page?: number; page_size?: number } = {}) =>
    api.get<PaginatedResponse<Order>>("/orders/my", { params }).then((r) => r.data),
};

export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }).then((r) => r.data),
  register: (email: string, password: string, first_name?: string, last_name?: string) =>
    api.post("/auth/register", { email, password, first_name, last_name }).then((r) => r.data),
  me: () => api.get<Customer>("/customers/me").then((r) => r.data),
};

export const wishlistApi = {
  get: () => api.get("/customers/me/wishlist").then((r) => r.data),
  add: (productId: string) => api.post(`/customers/me/wishlist/${productId}`).then((r) => r.data),
  remove: (productId: string) => api.delete(`/customers/me/wishlist/${productId}`).then((r) => r.data),
};

export const discountApi = {
  validate: (code: string, orderTotal: number) =>
    api.post("/marketplace/discount-codes/validate", null, { params: { code, order_total: orderTotal } }).then((r) => r.data),
};
