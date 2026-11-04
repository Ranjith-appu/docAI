import {
  AuthResponse,
  User,
  CaseItem,
  CaseDetail,
  DocumentItem,
  OCRResultData,
  ValidationResultData,
  TamperingResultData,
  FaceVerificationData,
  RiskAssessmentData,
  BlockchainRecordData,
  OfficerReviewData,
  BlockchainVerifyResponse,
  AuditLogItem,
  AnalyticsData,
} from "../types";

const API_BASE = "/api/v1";

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("docai_token");
}

export function setAuthToken(token: string, user: User) {
  if (typeof window === "undefined") return;
  localStorage.setItem("docai_token", token);
  localStorage.setItem("docai_user", JSON.stringify(user));
}

export function clearAuth() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("docai_token");
  localStorage.removeItem("docai_user");
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("docai_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      clearAuth();
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }
    let errorDetail = `HTTP ${res.status}`;
    try {
      const errorJson = await res.json();
      errorDetail = errorJson?.error?.message || errorJson?.detail || errorDetail;
    } catch {
      // Ignore
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // --- Auth ---
  async login(email: string, password: string): Promise<AuthResponse> {
    const data = await request<AuthResponse>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    setAuthToken(data.access_token, data.user);
    return data;
  },

  async getMe(): Promise<User> {
    return request<User>("/auth/me");
  },

  // --- Cases ---
  async getCases(status?: string, search?: string): Promise<CaseItem[]> {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (search) params.append("search", search);
    const query = params.toString() ? `?${params.toString()}` : "";
    return request<CaseItem[]>(`/cases${query}`);
  },

  async getCase(id: string): Promise<CaseDetail> {
    return request<CaseDetail>(`/cases/${id}`);
  },

  async createCase(applicant_name: string, document_type: string): Promise<CaseItem> {
    return request<CaseItem>("/cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ applicant_name, document_type }),
    });
  },

  // --- Documents ---
  async uploadDocument(caseId: string, documentType: string, file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append("document_type", documentType);
    formData.append("file", file);

    const token = getAuthToken();
    const res = await fetch(`${API_BASE}/cases/${caseId}/documents`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: { message: "Upload failed" } }));
      throw new Error(err?.error?.message || err?.detail || "Upload failed");
    }

    return res.json();
  },

  getDocumentFileUrl(documentId: string): string {
    return `${API_BASE}/documents/${documentId}/file`;
  },

  // --- Screening Pipeline ---
  async runOCR(documentId: string): Promise<OCRResultData> {
    return request<OCRResultData>(`/documents/${documentId}/ocr`, {
      method: "POST",
    });
  },

  async runValidation(caseId: string): Promise<ValidationResultData> {
    return request<ValidationResultData>(`/cases/${caseId}/validate`, {
      method: "POST",
    });
  },

  async runTampering(documentId: string): Promise<TamperingResultData> {
    return request<TamperingResultData>(`/documents/${documentId}/tampering-analysis`, {
      method: "POST",
    });
  },

  async runFaceVerification(caseId: string): Promise<FaceVerificationData> {
    return request<FaceVerificationData>(`/cases/${caseId}/face-verification`, {
      method: "POST",
    });
  },

  async runRiskAnalysis(caseId: string): Promise<RiskAssessmentData> {
    return request<RiskAssessmentData>(`/cases/${caseId}/risk-analysis`, {
      method: "POST",
    });
  },

  async registerBlockchain(caseId: string): Promise<BlockchainRecordData> {
    return request<BlockchainRecordData>(`/cases/${caseId}/blockchain/register`, {
      method: "POST",
    });
  },

  async submitReview(caseId: string, decision: string, notes?: string): Promise<OfficerReviewData> {
    return request<OfficerReviewData>(`/cases/${caseId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, notes }),
    });
  },

  async downloadReport(caseId: string, caseNumber: string) {
    const token = getAuthToken();
    const res = await fetch(`${API_BASE}/cases/${caseId}/report`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (!res.ok) throw new Error("Failed to download PDF report");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Screening_Report_${caseNumber}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  // --- Blockchain Verification ---
  async verifyBlockchain(payload: {
    case_number?: string;
    document_hash?: string;
  }): Promise<BlockchainVerifyResponse> {
    return request<BlockchainVerifyResponse>("/blockchain/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  // --- Analytics ---
  async getAnalytics(): Promise<AnalyticsData> {
    return request<AnalyticsData>("/analytics");
  },

  // --- Audit ---
  async getAuditLogs(caseId?: string, action?: string): Promise<AuditLogItem[]> {
    const params = new URLSearchParams();
    if (caseId) params.append("case_id", caseId);
    if (action) params.append("action", action);
    const query = params.toString() ? `?${params.toString()}` : "";
    return request<AuditLogItem[]>(`/audit-logs${query}`);
  },

  async verifyAuditChain(): Promise<{
    chain_intact: boolean;
    total_verified_entries: number;
    status: string;
    description: string;
  }> {
    return request("/audit-logs/verify-chain");
  },

  // --- Demo Seeding ---
  async seedDemoCases(): Promise<{
    success: boolean;
    message: string;
    cases: Array<{ case_number: string; profile: string; applicant: string }>;
  }> {
    return request("/demo/seed", {
      method: "POST",
    });
  },
};
