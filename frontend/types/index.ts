export type UserRole = "ADMIN" | "OFFICER" | "SUPERVISOR";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface DocumentField {
  field_name: string;
  field_value: string;
  confidence: number;
}

export interface DocumentItem {
  id: string;
  case_id: string;
  document_type: string;
  file_name: string;
  sha256_hash: string;
  mime_type: string;
  file_size: number;
  uploaded_at: string;
  fields: DocumentField[];
}

export interface CaseItem {
  id: string;
  case_number: string;
  applicant_name: string;
  document_type: string;
  status: "CREATED" | "PROCESSING" | "REVIEW_REQUIRED" | "VERIFIED" | "SUSPICIOUS" | "CLOSED";
  created_at: string;
  updated_at?: string;
}

export interface OCRFieldItem {
  field_name: string;
  value: string;
  confidence: number;
}

export interface OCRResultData {
  document_id: string;
  provider: string;
  raw_text: string;
  average_confidence: number;
  fields: Record<string, OCRFieldItem>;
}

export interface ValidationRuleItem {
  rule_name: string;
  passed: boolean;
  message: string;
  severity: "INFO" | "WARNING" | "ERROR";
}

export interface ValidationResultData {
  case_id: string;
  passed: boolean;
  rule_results: ValidationRuleItem[];
  errors: string[];
}

export interface SuspiciousRegionItem {
  region_type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  anomaly_score: number;
  indicator: string;
  explanation: string;
}

export interface TamperingResultData {
  document_id: string;
  tampering_score: number;
  confidence: number;
  detected_indicators: string[];
  suspicious_regions: SuspiciousRegionItem[];
  metadata_anomalies: string[];
  recommendation: string;
  explanation: string;
}

export interface FaceVerificationData {
  case_id: string;
  similarity_score: number;
  confidence: number;
  status: "MATCH" | "MISMATCH" | "UNABLE TO VERIFY";
  explanation: string;
}

export interface RiskFactorItem {
  factor_name: string;
  weight: number;
  contribution: number;
  description: string;
}

export interface RiskAssessmentData {
  case_id: string;
  overall_score: number;
  classification: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  contributing_factors: RiskFactorItem[];
  recommendation: string;
  summary_explanation: string;
}

export interface BlockchainRecordData {
  case_id: string;
  network: string;
  contract_address: string;
  tx_hash: string;
  block_number?: number;
  case_hash: string;
  document_hash: string;
  verification_hash: string;
  status: string;
  explorer_url?: string;
  created_at: string;
}

export interface OfficerReviewData {
  id: string;
  case_id: string;
  officer_id: string;
  officer_name?: string;
  decision: "VERIFIED" | "SUSPICIOUS" | "REJECTED" | "SUPERVISOR_REVIEW";
  notes?: string;
  reviewed_at: string;
}

export interface CaseDetail {
  case: CaseItem;
  documents: DocumentItem[];
  ocr_results: OCRResultData[];
  validation?: ValidationResultData;
  tampering_results: TamperingResultData[];
  face_verification?: FaceVerificationData;
  risk_assessment?: RiskAssessmentData;
  blockchain_record?: BlockchainRecordData;
  officer_review?: OfficerReviewData;
}

export interface BlockchainVerifyResponse {
  matched: boolean;
  status: "MATCH" | "DOES NOT MATCH" | "RECORD NOT FOUND";
  case_number: string;
  current_document_hash: string;
  blockchain_document_hash: string;
  blockchain_case_hash: string;
  block_timestamp?: string;
  risk_score?: number;
  network: string;
  contract_address: string;
  explorer_url?: string;
  details: string;
}

export interface AuditLogItem {
  id: string;
  case_id?: string;
  user_id?: string;
  action: string;
  prev_hash: string;
  entry_hash: string;
  timestamp: string;
  details: Record<string, any>;
}

export interface AnalyticsData {
  total_screenings: number;
  verified_count: number;
  suspicious_count: number;
  high_risk_count: number;
  manual_reviews_count: number;
  average_processing_seconds: number;
  tampering_detected_count: number;
  face_mismatch_count: number;
  blockchain_registrations_count: number;
  risk_distribution: Record<string, number>;
  document_type_distribution: Record<string, number>;
  daily_trend: Array<{ date: string; screenings: number }>;
}
