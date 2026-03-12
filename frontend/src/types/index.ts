export type VerificationStatus = "pending" | "processing" | "completed" | "failed";
export type VerificationModule = "private_credit" | "ai_ip_valuation";
export type AssetType = "training_data" | "model_weights" | "inference_infra" | "deployed_app";
export type ValuationMethod = "cost_approach" | "market_approach" | "income_approach";
export type UserRole = "owner" | "admin" | "analyst" | "viewer";
export type OrgPlan = "starter" | "professional" | "enterprise";
export type LLMProvider = "deepseek" | "openai" | "anthropic";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  domain: string | null;
  plan: OrgPlan;
  llm_provider: LLMProvider;
  llm_model: string;
  max_verifications_per_month: number;
  is_active: boolean;
  created_at: string;
  settings: Record<string, unknown>;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  last_login: string | null;
  mfa_enabled: boolean;
  organization: Organization;
  created_at: string;
}

export interface Verification {
  id: string;
  organization_id: string;
  created_by: string;
  module: VerificationModule;
  status: VerificationStatus;
  input_data: Record<string, unknown>;
  result_data: Record<string, unknown> | null;
  proof_hash: string | null;
  proof_certificate_url: string | null;
  report_url: string | null;
  metadata: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  creator?: User;
}

export interface CreditPortfolio {
  id: string;
  organization_id: string;
  verification_id: string;
  portfolio_name: string;
  fund_name: string;
  loan_count: number;
  total_principal: number;
  weighted_avg_rate: number;
  avg_ltv_ratio: number;
  nav_value: number;
  covenant_compliance_status: Record<string, unknown>;
  created_at: string;
}

export interface AIAsset {
  id: string;
  organization_id: string;
  verification_id: string;
  asset_type: AssetType;
  asset_name: string;
  description: string;
  valuation_method: ValuationMethod;
  estimated_value: number;
  confidence_score: number;
  valuation_inputs: Record<string, unknown>;
  valuation_breakdown: Record<string, unknown>;
  ias38_compliant: boolean;
  asc350_compliant: boolean;
  created_at: string;
}

export interface AuditLog {
  id: string;
  organization_id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  ip_address: string;
  user_agent: string;
  timestamp: string;
  user?: User;
}

export interface DashboardStats {
  total_verifications: number;
  completed_verifications: number;
  pending_verifications: number;
  failed_verifications: number;
  total_asset_value: number;
  credit_portfolios: number;
  ai_assets: number;
  monthly_usage: number;
  monthly_limit: number;
  recent_verifications: Verification[];
  verification_trend: { date: string; count: number }[];
  value_by_module: { module: string; value: number }[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface BillingInfo {
  plan: OrgPlan;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  current_period_end: string | null;
  usage_this_month: number;
  usage_limit: number;
  invoices: Invoice[];
}

export interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
  pdf_url: string;
}

export interface LoanTapeEntry {
  loan_id: string;
  borrower_id: string;
  principal: number;
  interest_rate: number;
  term_months: number;
  origination_date: string;
  maturity_date: string;
  collateral_value: number;
  collateral_type: string;
  payment_status: string;
  outstanding_balance: number;
  ltv_ratio?: number;
  dscr?: number;
}

export interface AIAssetInput {
  asset_name: string;
  asset_type: AssetType;
  description: string;
  cloud_provider?: string;
  training_compute_hours?: number;
  training_cost?: number;
  dataset_size_gb?: number;
  dataset_uniqueness_score?: number;
  model_parameters?: number;
  benchmark_scores?: Record<string, number>;
  monthly_revenue?: number;
  monthly_active_users?: number;
  inference_cost_per_query?: number;
  gpu_type?: string;
  gpu_count?: number;
}
