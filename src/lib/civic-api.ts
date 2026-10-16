export type CivicRole = "citizen" | "admin" | "officer";
export type ComplaintStatus =
  "Submitted" | "Under Review" | "Assigned" | "In Progress" | "Resolved";
export type Priority = "Low" | "Medium" | "High" | "Critical";
export type CivicUser = {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  ward: string | null;
  role: CivicRole;
  department_id: number | null;
  department: string | null;
};
export type AuthResponse = { access_token: string; token_type: string; user: CivicUser };
export type Complaint = {
  id: string;
  title: string;
  description: string;
  category: string;
  status: ComplaintStatus;
  priority: Priority;
  location: string;
  department: string;
  citizen: string;
  officer: string;
  date: string;
  lat: number | null;
  lng: number | null;
  duplicate?: string | null;
  aiReason: string;
  history?: {
    previous_status: string | null;
    new_status: string;
    note: string | null;
    changed_by: string;
    created_at: string;
  }[];
  comments?: { id: number; author: string; body: string; created_at: string }[];
  attachments?: {
    id: number;
    original_name: string;
    content_type: string;
    size_bytes: number;
    url: string;
    created_at: string;
  }[];
};
export type Category = { name: string; icon: string; count: number };
export type NotificationItem = {
  id: number;
  complaint_id: string | null;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
};
export type DashboardStats = {
  total: number;
  open: number;
  in_progress: number;
  resolved: number;
  critical: number;
  needs_attention: number;
  by_status: Record<string, number>;
  by_category: { name: string; value: number }[];
  by_priority: Record<string, number>;
  weekly: { day: string; date: string; filed: number; resolved: number }[];
  satisfaction: number | null;
};
export type Department = { id: number; name: string };
export type Officer = {
  id: number;
  name: string;
  email: string;
  department_id: number | null;
  department: string | null;
};
export type ComplaintFilters = {
  q?: string;
  status?: string;
  category?: string;
  priority?: string;
  department_id?: number;
  officer_id?: number;
  date_from?: string;
  date_to?: string;
  sort_by?: "created_at" | "status" | "priority" | "category";
  order?: "asc" | "desc";
  page?: number;
  page_size?: number;
};
type Envelope<T> = { data: T; meta?: Record<string, number> };
const apiBase = (import.meta.env["VITE_API_URL"] || "http://localhost:8000/api").replace(/\/$/, "");
const tokenKey = "civicpulse.access-token";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
function token() {
  return typeof window === "undefined" ? null : window.localStorage.getItem(tokenKey);
}
export function saveToken(value: string | null) {
  if (typeof window === "undefined") return;
  if (value) window.localStorage.setItem(tokenKey, value);
  else window.localStorage.removeItem(tokenKey);
}
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  const accessToken = token();
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${apiBase}${path}`, { ...init, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = (await response.json()) as { error?: { message?: string }; detail?: string };
      message = payload.error?.message ?? payload.detail ?? message;
    } catch {
      /* Keep the HTTP status if the response is not JSON. */
    }
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as T;
}
function encodeQuery(values: Record<string, string | number | undefined>) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}
function mapComplaint(raw: Record<string, unknown>): Complaint {
  return {
    ...(raw as unknown as Complaint),
    date: String(raw["date"] ?? raw["created_at"] ?? ""),
    lat: typeof raw["latitude"] === "number" ? raw["latitude"] : null,
    lng: typeof raw["longitude"] === "number" ? raw["longitude"] : null,
    aiReason: String(raw["ai_reason"] ?? ""),
  };
}

export const civicApi = {
  async login(email: string, password: string) {
    const response = await request<Envelope<AuthResponse>>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    saveToken(response.data.access_token);
    return response.data;
  },
  async register(input: {
    name: string;
    email: string;
    password: string;
    phone?: string;
    ward?: string;
    role?: CivicRole;
    invitation_code?: string;
  }) {
    const response = await request<Envelope<AuthResponse>>("/auth/register", {
      method: "POST",
      body: JSON.stringify(input),
    });
    saveToken(response.data.access_token);
    return response.data;
  },
  async logout() {
    try {
      await request("/auth/logout", { method: "POST" });
    } finally {
      saveToken(null);
    }
  },
  async me() {
    return (await request<Envelope<CivicUser>>("/auth/me")).data;
  },
  async updateProfile(input: { name?: string; phone?: string | null; ward?: string | null }) {
    return (
      await request<Envelope<CivicUser>>("/auth/me", {
        method: "PATCH",
        body: JSON.stringify(input),
      })
    ).data;
  },
  async complaints(filters: ComplaintFilters = {}) {
    const response = await request<
      Envelope<Record<string, unknown>[]> & {
        meta: { page: number; page_size: number; total: number; pages: number };
      }
    >(`/complaints${encodeQuery(filters)}`);
    return { ...response, data: response.data.map(mapComplaint) };
  },
  async complaint(id: string) {
    return mapComplaint(
      (await request<Envelope<Record<string, unknown>>>(`/complaints/${encodeURIComponent(id)}`))
        .data,
    );
  },
  async trackComplaint(id: string) {
    return (
      await request<
        Envelope<{
          id: string;
          title: string;
          category: string;
          status: ComplaintStatus;
          date: string;
          history: Complaint["history"];
        }>
      >(`/complaints/${encodeURIComponent(id)}/track`)
    ).data;
  },
  async createComplaint(input: {
    title: string;
    description: string;
    category?: string;
    location: string;
    latitude?: number;
    longitude?: number;
  }) {
    const response = await request<Envelope<Record<string, unknown>>>("/complaints", {
      method: "POST",
      body: JSON.stringify(input),
    });
    const complaint = mapComplaint(response.data);
    return complaint;
  },
  async assignComplaint(id: string, department_id: number, officer_id: number | null) {
    return mapComplaint(
      (
        await request<Envelope<Record<string, unknown>>>(
          `/complaints/${encodeURIComponent(id)}/assign`,
          { method: "POST", body: JSON.stringify({ department_id, officer_id }) },
        )
      ).data,
    );
  },
  async updateStatus(id: string, status: ComplaintStatus, note?: string) {
    return mapComplaint(
      (
        await request<Envelope<Record<string, unknown>>>(
          `/complaints/${encodeURIComponent(id)}/status`,
          { method: "PATCH", body: JSON.stringify({ status, note }) },
        )
      ).data,
    );
  },
  async analyze(input: { title: string; description: string; category?: string }) {
    return (
      await request<
        Envelope<{
          category: { category: string; confidence: number; explanation: string };
          priority: { priority: Priority; explanation: string };
          possible_duplicates: { complaint_id?: string; similarity: number }[];
          review_required: boolean;
        }>
      >("/ai/analyze", { method: "POST", body: JSON.stringify(input) })
    ).data;
  },
  async categories() {
    return (await request<Envelope<Category[]>>("/ai/categories")).data;
  },
  async dashboard() {
    return (await request<Envelope<DashboardStats>>("/dashboard/stats")).data;
  },
  async departments() {
    return (await request<Envelope<Department[]>>("/departments")).data;
  },
  async officers() {
    return (await request<Envelope<Officer[]>>("/officers")).data;
  },
  async notifications() {
    return request<Envelope<NotificationItem[]> & { meta: { unread: number } }>("/notifications");
  },
  async markAllRead() {
    return request<Envelope<{ updated: number }>>("/notifications/read-all", { method: "PATCH" });
  },
  async markNotificationRead(id: number) {
    return request<Envelope<{ id: number; is_read: boolean }>>(`/notifications/${id}/read`, {
      method: "PATCH",
    });
  },
  async submitFeedback(input: { rating: number; comments?: string; complaint_id?: string }) {
    return request<Envelope<{ id: number }>>("/feedback", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },
  async uploadImage(id: string, image: File) {
    const body = new FormData();
    body.set("file", image);
    return request<Envelope<{ id: number; url: string }>>(
      `/complaints/${encodeURIComponent(id)}/attachments`,
      { method: "POST", body },
    );
  },
  async exportCsv() {
    const accessToken = token();
    const response = await fetch(`${apiBase}/complaints/export.csv`, {
      headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
    });
    if (!response.ok)
      throw new ApiError(`Report export failed (${response.status})`, response.status);
    return response.blob();
  },
};
