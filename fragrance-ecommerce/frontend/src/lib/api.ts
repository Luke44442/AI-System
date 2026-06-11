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
  forgotPassword: (email: string) =>
    api.post("/auth/forgot-password", { email }).then((r) => r.data),
  resetPassword: (token: string, new_password: string) =>
    api.post("/auth/reset-password", { token, new_password }).then((r) => r.data),
};

export interface CheckoutLineItem { product_id: string; quantity: number }
export interface OrderQuote {
  subtotal: number; shipping: number; tax: number; discount: number; total: number;
  discount_valid?: boolean; discount_message?: string | null;
}

export const checkoutApi = {
  quote: (items: CheckoutLineItem[], shipping_address?: object, discount_code?: string) =>
    api.post<OrderQuote>("/checkout/quote", { items, shipping_address, discount_code }).then((r) => r.data),
  createPaymentIntent: (payload: object) =>
    api.post("/checkout/create-payment-intent", payload).then((r) => r.data),
};

export const wishlistApi = {
  get: () => api.get("/customers/me/wishlist").then((r) => r.data),
  add: (productId: string) => api.post(`/customers/me/wishlist/${productId}`).then((r) => r.data),
  remove: (productId: string) => api.delete(`/customers/me/wishlist/${productId}`).then((r) => r.data),
};

interface ItemsResponse { items: Product[] }

export const recommendationsApi = {
  similar: (productId: string, limit = 8) =>
    api.get<ItemsResponse>(`/recommendations/similar/${productId}`, { params: { limit } }).then((r) => r.data.items),
  frequentlyBoughtTogether: (productId: string, limit = 4) =>
    api.get<ItemsResponse>(`/recommendations/frequently-bought-together/${productId}`, { params: { limit } }).then((r) => r.data.items),
  completeTheLook: (productId: string, limit = 6) =>
    api.get<ItemsResponse>(`/recommendations/complete-the-look/${productId}`, { params: { limit } }).then((r) => r.data.items),
  trending: (limit = 12, category_slug?: string) =>
    api.get<ItemsResponse>(`/recommendations/trending`, { params: { limit, category_slug } }).then((r) => r.data.items),
  bestsellers: (limit = 12, category_slug?: string) =>
    api.get<ItemsResponse>(`/recommendations/bestsellers`, { params: { limit, category_slug } }).then((r) => r.data.items),
  recentlyViewed: (product_ids: string[]) =>
    api.post<ItemsResponse>(`/recommendations/recently-viewed`, { product_ids }).then((r) => r.data.items),
};

export interface AssistantResponse {
  message: string;
  intent: Record<string, unknown>;
  items: Product[];
}

export const assistantApi = {
  recommend: (query: string, limit = 12) =>
    api.post<AssistantResponse>(`/assistant/recommend`, { query, limit }).then((r) => r.data),
};

export const discountApi = {
  validate: (code: string, orderTotal: number) =>
    api.post("/marketplace/discount-codes/validate", null, { params: { code, order_total: orderTotal } }).then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Analytics (admin)
// ---------------------------------------------------------------------------

export interface ProfitDashboard {
  profit_7d: number; profit_30d: number;
  revenue_7d: number; revenue_30d: number;
  orders_7d: number; orders_30d: number;
  avg_margin_30d: number;
}

export interface ProfitabilityRow {
  order_id: string; order_number: string; order_date: string;
  revenue: number; supplier_cost: number; shipping_cost: number;
  platform_fee: number; stripe_fee: number;
  gross_profit: number; net_profit: number;
  margin_pct: number; channel: string;
}

export interface ProfitabilityResponse {
  items: ProfitabilityRow[];
  summary: {
    total_revenue: number; total_profit: number; avg_margin_pct: number;
    by_channel: Record<string, { revenue: number; profit: number; orders: number }>;
  };
}

export interface PricingAlert {
  id: string; product_id: string; alert_type: string;
  message: string; current_value: number; threshold_value: number;
  is_resolved: boolean; created_at: string;
}

export const analyticsApi = {
  dashboard: () =>
    api.get<ProfitDashboard>("/analytics/dashboard/profit").then((r) => r.data),
  profitability: (params?: { from_date?: string; to_date?: string; channel?: string; limit?: number }) =>
    api.get<ProfitabilityResponse>("/analytics/profitability", { params }).then((r) => r.data),
  pricingAlerts: () =>
    api.get<{ items: PricingAlert[] }>("/analytics/pricing-alerts").then((r) => r.data),
  resolveAlert: (alertId: string) =>
    api.post(`/analytics/pricing-alerts/${alertId}/resolve`).then((r) => r.data),
};

// ---------------------------------------------------------------------------
// System health, supplier queue, marketplace sync (admin)
// ---------------------------------------------------------------------------

export interface SystemEventRow {
  id: string; event_type: string; severity: string;
  message: string | null; payload?: Record<string, unknown>;
  order_id: string | null; listing_id: string | null; product_id: string | null;
  created_at: string | null;
}

export interface FailuresDashboard {
  counts: {
    failed_supplier_orders: number;
    supplier_queue_backlog: number;
    dead_letter_listings: number;
    retrying_listings: number;
    orphaned_paid_orders: number;
  };
  healthy: boolean;
  recent_errors: SystemEventRow[];
}

export interface SupplierQueueItem {
  id: string; order_id: string; order_number: string | null;
  order_total: string | null; customer_name: string | null;
  supplier_id: string | null; status: string;
  external_order_id: string | null; external_status: string | null;
  tracking_number: string | null;
  failure_reason: string | null; queued_reason: string | null;
  attempts: number; last_attempt_at: string | null; created_at: string | null;
}

export interface DeadLetterRow {
  id: string; listing_id: string | null; product_id: string | null;
  platform: string; operation: string; attempts: number;
  last_error: string | null; is_resolved: boolean; created_at: string | null;
}

export const systemApi = {
  failures: () => api.get<FailuresDashboard>("/system/failures").then((r) => r.data),
  events: (params?: { severity?: string; event_type?: string; order_id?: string; limit?: number }) =>
    api.get<{ items: SystemEventRow[] }>("/system/events", { params }).then((r) => r.data),
  supplierQueue: (status?: string) =>
    api.get<{ items: SupplierQueueItem[]; count: number }>("/system/supplier-queue", { params: { status } }).then((r) => r.data),
  retryQueueItem: (id: string) =>
    api.post<SupplierQueueItem>(`/system/supplier-queue/${id}/retry`).then((r) => r.data),
  resolveQueueItem: (id: string, external_order_id?: string, note?: string) =>
    api.post<SupplierQueueItem>(`/system/supplier-queue/${id}/resolve`, { external_order_id, note }).then((r) => r.data),
  deadLetters: () =>
    api.get<{ items: DeadLetterRow[] }>("/system/dead-letters").then((r) => r.data),
  retryDeadLetter: (id: string) =>
    api.post(`/system/dead-letters/${id}/retry`).then((r) => r.data),
  resolveDeadLetter: (id: string) =>
    api.post(`/system/dead-letters/${id}/resolve`).then((r) => r.data),
};

export interface MarketplaceListingRow {
  id: string; product_id: string; platform: string;
  listing_id: string | null; status: string; price: string | null;
  listing_url: string | null; last_synced_at: string | null;
}

export interface PlatformStatus {
  platform: string;
  configured: boolean;
  supports_inventory_sync: boolean;
  supports_price_sync: boolean;
  supports_order_sync: boolean;
}

export interface MarketplaceHealth {
  platforms: PlatformStatus[];
  listing_counts: Record<string, Record<string, number>>;
  recent_failures: {
    platform: string; product_id: string; status?: string;
    attempts?: number; error: string | null; next_retry_at?: string | null;
    last_synced_at: string | null;
  }[];
  dead_letter_count: number;
}

export const marketplaceApi = {
  status: () => api.get<MarketplaceHealth>("/marketplace/status").then((r) => r.data),
  listings: (params?: { platform?: string; status?: string; page?: number; page_size?: number }) =>
    api.get<PaginatedResponse<MarketplaceListingRow>>("/marketplace/listings", { params }).then((r) => r.data),
  syncProduct: (productId: string) =>
    api.post(`/marketplace/sync/${productId}`).then((r) => r.data),
  syncAll: () => api.post("/marketplace/sync-all").then((r) => r.data),
};

export interface AdminOrderRow {
  id: string; order_number: string; customer_id: string | null;
  customer_name: string | null; channel: string; status: string;
  payment_status: string; fulfillment_status: string;
  total: number; currency: string; item_count: number;
}

export const adminApi = {
  orders: (params?: { search?: string; status?: string; payment_status?: string; channel?: string; page?: number; page_size?: number }) =>
    api.get<PaginatedResponse<AdminOrderRow>>("/orders", { params }).then((r) => r.data),
  order: (id: string) => api.get<Order>(`/orders/${id}`).then((r) => r.data),
  fulfillOrder: (id: string) => api.post(`/orders/${id}/fulfill`).then((r) => r.data),
  setTracking: (id: string, tracking_number: string, carrier?: string) =>
    api.post(`/orders/${id}/tracking`, { tracking_number, carrier }).then((r) => r.data),
  customers: (params?: { search?: string; page?: number; page_size?: number }) =>
    api.get<{ items: { id: string; email: string; first_name: string | null; last_name: string | null; order_count: number; total_spent: string; is_active: boolean; marketing_consent: boolean; created_at: string | null }[]; total: number }>("/customers", { params }).then((r) => r.data),
  products: (params?: ProductParams) =>
    api.get<PaginatedResponse<Product>>("/products", { params }).then((r) => r.data),
  uploadProductImage: (file: File, productId?: string, isPrimary = false) => {
    const form = new FormData();
    form.append("file", file);
    const params = new URLSearchParams();
    if (productId) params.set("product_id", productId);
    if (isPrimary) params.set("is_primary", "true");
    return api.post(`/upload/product-image?${params.toString()}`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
};

export interface EmailSubscriberRow {
  id: string; email: string; first_name: string | null;
  status: string; source: string | null; subscribed_at: string | null;
  open_count: number; click_count: number;
}

export const emailAdminApi = {
  subscriberCount: () =>
    api.get<{ total: number; subscribed: number; unsubscribed: number; bounced: number }>("/email/subscribers/count").then((r) => r.data),
  subscribers: (params?: { status?: string; limit?: number; offset?: number }) =>
    api.get<{ total: number; items: EmailSubscriberRow[] }>("/email/subscribers", { params }).then((r) => r.data),
  runAutomation: (name: "cart-abandonment" | "review-requests" | "win-back") =>
    api.post<{ task_id: string; status: string }>(`/email/automations/${name}/run`).then((r) => r.data),
  sendTest: (to: string, template = "welcome") =>
    api.post("/email/test", { to, template }).then((r) => r.data),
};
