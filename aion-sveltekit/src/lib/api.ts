/**
 * EchoWorks API Client
 * Connects SvelteKit frontend to Django backend
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface FetchOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  token?: string;
}

async function api<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (options.token) {
    headers['Authorization'] = `Bearer ${options.token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || error.message || 'API request failed');
  }

  return res.json();
}

// ============================================================================
// CATALOG API
// ============================================================================

export interface Product {
  id: number;
  name: string;
  slug: string;
  tagline: string;
  hero_image: string | null;
  category_name: string;
  category_slug: string;
  status: 'active' | 'coming_soon';
  is_featured: boolean;
  features: string[];
  use_cases: string[];
  starting_price: {
    amount: number | null;
    cycle: string;
    currency: string;
  };
}

export interface ProductDetail extends Product {
  description: string;
  pricing_tiers: PricingTier[];
  screenshots: { id: number; image: string; caption: string }[];
}

export interface PricingTier {
  id: number;
  name: string;
  price: number | null;
  price_display: string;
  billing_cycle: string;
  features_included: string[];
  is_popular: boolean;
  stripe_price_id: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  product_count: number;
}

export const catalog = {
  getProducts: () => api<Product[]>('/catalog/products/'),
  getProduct: (slug: string) => api<ProductDetail>(`/catalog/products/${slug}/`),
  getFeatured: () => api<Product[]>('/catalog/featured/'),
  getCategories: () => api<Category[]>('/catalog/categories/'),
};

// ============================================================================
// DEMOS API — Live product demonstrations
// ============================================================================

export interface DocumentAnalyzeInput {
  document_text: string;
  document_type?: 'contract' | 'agreement' | 'nda' | 'employment' | 'license' | 'other';
}

export interface DocumentAnalyzeResult {
  document_type: string;
  risk_score: number;
  risk_level: string;
  summary: string;
  clauses_found: number;
  clauses: {
    clause_type: string;
    text: string;
    risk_level: string;
    explanation: string;
    recommendation: string;
  }[];
  obligations: { party: string; obligation: string; risk: string }[];
  red_flags: string[];
  processing_time_ms: number;
}

export interface ThreatProfileResult {
  risk_score: number;
  risk_level: string;
  reasoning_summary: string;
  deviation_alerts: { indicator: string; count: number; severity: string; details: string }[];
  trend_30_60_90: Record<string, number>;
  recommended_actions: string[];
  peer_comparison: { firm_average: number; percentile: number };
  processing_time_ms: number;
}

export interface AgentChatInput {
  message: string;
  context?: 'security_analyst' | 'legal_advisor' | 'compliance_officer';
  conversation_id?: string;
}

export interface AgentChatResult {
  response: string;
  context: string;
  conversation_id: string;
  sources: string[];
  confidence: number;
  processing_time_ms: number;
}

export const demos = {
  analyzeDocument: (input: DocumentAnalyzeInput) =>
    api<DocumentAnalyzeResult>('/demos/document-analyze/', { method: 'POST', body: input }),

  getThreatProfile: (scenario: string) =>
    api<ThreatProfileResult>('/demos/threat-profile/', { method: 'POST', body: { scenario } }),

  chatWithAgent: (input: AgentChatInput) =>
    api<AgentChatResult>('/demos/agent-chat/', { method: 'POST', body: input }),
};

// ============================================================================
// LEADS API — Newsletter, Contact, ROI Calculator
// ============================================================================

export interface ROIInput {
  company_size?: number;
  avg_contract_value?: number;
  contracts_per_month?: number;
  hours_per_contract?: number;
  hourly_rate?: number;
}

export interface ROIResult {
  annual_savings: number;
  monthly_savings: number;
  hours_saved: number;
  roi_percentage: number;
  payback_months: number;
  current_cost: number;
  aion_cost: number;
}

export const leads = {
  subscribeNewsletter: (email: string, firstName?: string) =>
    api('/leads/newsletter/', { method: 'POST', body: { email, first_name: firstName } }),

  submitContact: (data: { name: string; email: string; company?: string; message?: string }) =>
    api('/leads/contact/', { method: 'POST', body: data }),

  calculateROI: (input: ROIInput) =>
    api<ROIResult>('/leads/roi-calculate/', { method: 'POST', body: input }),
};

// ============================================================================
// BOOKINGS API
// ============================================================================

export interface DemoRequestInput {
  name: string;
  email: string;
  company: string;
  job_title?: string;
  company_size?: string;
  products_interested?: string[];
  preferred_date?: string;
  preferred_time?: string;
  message?: string;
}

export const bookings = {
  requestDemo: (data: DemoRequestInput) =>
    api('/bookings/request/', { method: 'POST', body: data }),

  submitContact: (data: { name: string; email: string; company?: string; message?: string }) =>
    api('/leads/contact/', { method: 'POST', body: data }),

  getAvailability: () =>
    api('/bookings/availability/'),
};

// ============================================================================
// PAYMENTS API
// ============================================================================

export const payments = {
  createCheckout: (pricingTierId: number, customerEmail: string, customerName: string) =>
    api<{ checkout_url: string; session_id: string }>('/payments/checkout/', {
      method: 'POST',
      body: { pricing_tier_id: pricingTierId, customer_email: customerEmail, customer_name: customerName },
    }),
};

// ============================================================================
// BLOG & CASE STUDIES API
// ============================================================================

export const blog = {
  getPosts: () => api('/blog/posts/'),
  getPost: (slug: string) => api(`/blog/posts/${slug}/`),
};

export const caseStudies = {
  getStudies: () => api('/casestudies/studies/'),
  getStudy: (slug: string) => api(`/casestudies/studies/${slug}/`),
  getTestimonials: () => api('/casestudies/testimonials/'),
};
