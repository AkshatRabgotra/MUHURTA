import type {
  FunnelData,
  HealthResponse,
  PaginatedResponse,
  PlanRequest,
  Slot,
  TelegramLinkResponse,
  UnmappedRequestGroup,
  User,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiClient {
  public baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  async fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('muhurta_token') : null;
    const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
        ...options?.headers,
      },
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({
        error: { code: 'unknown', message: res.statusText },
      }));
      throw new ApiError(
        res.status,
        error.error?.code || 'unknown',
        error.error?.message || res.statusText,
      );
    }

    return res.json();
  }

  getHealth(): Promise<HealthResponse> {
    return this.fetch<HealthResponse>('/health');
  }

  createPlan(text: string, category?: string): Promise<PlanRequest> {
    return this.fetch<PlanRequest>('/plans', {
      method: 'POST',
      body: JSON.stringify({ text, category }),
    });
  }

  getPlans(page: number = 1, pageSize: number = 10): Promise<PaginatedResponse<PlanRequest>> {
    return this.fetch<PaginatedResponse<PlanRequest>>(`/plans?page=${page}&page_size=${pageSize}`);
  }

  getPlan(id: string): Promise<PlanRequest> {
    return this.fetch<PlanRequest>(`/plans/${id}`);
  }

  addToCalendar(slotId: string): Promise<{ calendar_event_id: string; google_event_id?: string; message: string }> {
    return this.fetch<{ calendar_event_id: string; google_event_id?: string; message: string }>(
      `/slots/${slotId}/calendar`,
      { method: 'POST' },
    );
  }

  submitFeedback(slotId: string, rating: 1 | -1, comment?: string): Promise<{ id: string; rating: number }> {
    return this.fetch<{ id: string; rating: number }>(`/slots/${slotId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ rating, comment }),
    });
  }

  getMe(): Promise<User> {
    return this.fetch<User>('/me');
  }

  updateMe(data: { timezone?: string; default_city?: string }): Promise<User> {
    return this.fetch<User>('/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  linkTelegram(): Promise<TelegramLinkResponse> {
    return this.fetch<TelegramLinkResponse>('/me/telegram/link', {
      method: 'POST',
    });
  }

  devLogin(): Promise<{ message: string; user: User; token: string }> {
    return this.fetch<{ message: string; user: User; token: string }>('/auth/dev-login', {
      method: 'POST',
    });
  }

  async register(data: { email: string; password: string; name?: string; timezone?: string; default_city?: string }): Promise<{ message: string; user: User; token: string }> {
    const res = await this.fetch<{ message: string; user: User; token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (res.token && typeof window !== 'undefined') {
      localStorage.setItem('muhurta_token', res.token);
    }
    return res;
  }

  async login(data: { email: string; password: string }): Promise<{ message: string; user: User; token: string }> {
    const res = await this.fetch<{ message: string; user: User; token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (res.token && typeof window !== 'undefined') {
      localStorage.setItem('muhurta_token', res.token);
    }
    return res;
  }

  async logout(): Promise<{ message: string }> {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('muhurta_token');
    }
    return this.fetch<{ message: string }>('/auth/logout', {
      method: 'POST',
    });
  }

  getGoogleLoginUrl(): string {
    return `${this.baseUrl}/auth/google/login`;
  }

  getFunnel(): Promise<{ variants: FunnelData[] }> {
    return this.fetch<{ variants: FunnelData[] }>('/analytics/funnel');
  }

  getUnmappedAnalytics(): Promise<UnmappedRequestGroup[]> {
    return this.fetch<UnmappedRequestGroup[]>('/analytics/unmapped');
  }
}

export const api = new ApiClient();

/** Utility to generate and download universal .ics iCalendar file */
export function downloadSlotIcs(slot: Slot, title: string, location: string = 'Bengaluru') {
  const formatIcsDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
  };

  const start = formatIcsDate(slot.start_utc);
  const end = formatIcsDate(slot.end_utc);
  const summary = `Auspicious Muhurta: ${title}`;
  const description = `${slot.explanation_text || 'Vedic Auspicious Time Window'}\\nScore: ${slot.score} pts`;

  const icsContent = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Muhurta Planner//Vedic Muhurta//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:muhurta-${slot.id}@vedicmuhurta.app`,
    `DTSTAMP:${formatIcsDate(new Date().toISOString())}`,
    `DTSTART:${start}`,
    `DTEND:${end}`,
    `SUMMARY:${summary}`,
    `DESCRIPTION:${description}`,
    `LOCATION:${location}`,
    'STATUS:CONFIRMED',
    'END:VEVENT',
    'END:VCALENDAR',
  ].join('\r\n');

  const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `muhurta-${slot.id.slice(0, 8)}.ics`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
