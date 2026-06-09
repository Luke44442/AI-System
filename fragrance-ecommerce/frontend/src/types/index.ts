export interface Brand {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
  is_luxury: boolean;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  image_url?: string;
  product_count: number;
  children?: Category[];
}

export interface ProductVariant {
  id: string;
  sku: string;
  name: string;
  volume_ml?: number;
  website_price?: number;
  marketplace_price?: number;
  inventory_quantity: number;
  is_active: boolean;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  slug: string;
  brand?: Brand;
  brand_id?: string;
  category_id?: string;
  description?: string;
  short_description?: string;
  fragrance_family?: string;
  concentration?: string;
  gender: "male" | "female" | "unisex";
  volume_ml?: number;
  launch_year?: number;
  top_notes?: string[];
  middle_notes?: string[];
  base_notes?: string[];
  supplier_cost?: number;
  website_price?: number;
  marketplace_price?: number;
  compare_at_price?: number;
  inventory_status: "in_stock" | "low_stock" | "out_of_stock";
  inventory_quantity: number;
  images?: { url: string; alt?: string }[];
  tags?: string[];
  is_active: boolean;
  is_featured: boolean;
  is_bestseller: boolean;
  is_new_arrival: boolean;
  rating_avg?: number;
  review_count: number;
  variants: ProductVariant[];
}

export interface Collection {
  id: string;
  name: string;
  slug: string;
  description?: string;
  image_url?: string;
  banner_url?: string;
  is_featured: boolean;
}

export interface CartItem {
  id: string;
  product_id: string;
  variant_id?: string;
  quantity: number;
  product?: Product;
  variant?: ProductVariant;
}

export interface Cart {
  id: string;
  session_token: string;
  items: CartItem[];
  coupon_code?: string;
}

export interface Order {
  id: string;
  order_number: string;
  status: string;
  payment_status: string;
  fulfillment_status: string;
  subtotal: number;
  shipping_amount: number;
  tax_amount: number;
  discount_amount: number;
  total: number;
  currency: string;
  items: OrderItem[];
  shipping_address?: Address;
  tracking_number?: string;
  tracking_url?: string;
}

export interface OrderItem {
  id: string;
  sku: string;
  name: string;
  image_url?: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface Address {
  first_name: string;
  last_name: string;
  address1: string;
  address2?: string;
  city: string;
  state?: string;
  postal_code: string;
  country: string;
  phone?: string;
}

export interface Customer {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_admin: boolean;
  order_count: number;
  total_spent: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface FilterState {
  search?: string;
  brand_id?: string;
  category_id?: string;
  gender?: string;
  concentration?: string;
  min_price?: number;
  max_price?: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
}
