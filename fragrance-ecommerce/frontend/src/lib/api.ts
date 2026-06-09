import axios from "axios";
import type { Product, PaginatedResponse, Collection, Category, Brand, Order, Customer } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("scentara_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("scentara_token");
    }
    return Promise.reject(error);
  }
);

export interface ProductParams {
  page?: number;
  page_size?: number;
  search?: string;
  brand_id?: string;
  category_id?: string;
  gender?: string;
  concentration?: string;
  is_featured?: boolean;
  min_price?: number;
  max_price?: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
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
};

export const brandsApi = {
  list: () => api.get<Brand[]>("/brands").then((r) => r.data),
};

export const ordersApi = {
  create: (data: object) => api.post<Order>("/orders", data).then((r) => r.data),
  get: (id: string) => api.get<Order>(`/orders/${id}`).then((r) => r.data),
  myOrders: (page = 1) => api.get<PaginatedResponse<Order>>("/orders/my", { params: { page } }).then((r) => r.data),
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
