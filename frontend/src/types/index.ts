/** Reason for a particular slot's score. */
export interface SlotReason {
  factor: string;
  value: string;
  points: number;
}

export interface ClarificationOption {
  label: string;
  category: string;
  description?: string;
}

export interface Clarification {
  question: string;
  options: ClarificationOption[];
}

/** A candidate time-slot with its auspiciousness score. */
export interface Slot {
  id: string;
  start_utc: string;
  end_utc: string;
  score: number;
  rank: number;
  explanation_text: string | null;
  reasons: SlotReason[];
}

/** A plan request created by the user. */
export interface PlanRequest {
  id: string;
  user_id?: string;
  raw_text: string;
  category?: string;
  override?: string | null;
  confidence?: number;
  basis?: string;
  runner_up_category?: string | null;
  advisory_note?: string | null;
  shortage_reason?: string | null;
  clarification?: Clarification | null;
  event_type: string | null;
  location_name?: string | null;
  lat?: number | null;
  lon?: number | null;
  timezone?: string | null;
  prompt_variant?: string | null;
  status: string;
  created_at: string;
  slots: Slot[];
}

/** Authenticated user profile. */
export interface User {
  id: string;
  email: string;
  name: string;
  timezone: string;
  default_city?: string | null;
  telegram_chat_id: string | null;
}

/** Response from the /health endpoint. */
export interface HealthResponse {
  status: string;
  database: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface FunnelData {
  prompt_variant: string;
  request_created: number;
  slots_viewed: number;
  slot_added_to_calendar: number;
  reminder_sent: number;
  feedback_given: number;
  conversion_rate_viewed_to_calendar: number;
}

export interface TelegramLinkResponse {
  code: string;
  deep_link: string;
}

export interface UnmappedRequestGroup {
  keyword: string;
  count: number;
  newest_request: string;
  last_created_at: string;
  sample_requests: string[];
}

