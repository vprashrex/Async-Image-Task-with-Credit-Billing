// API Types
export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_admin: boolean;
  credits: number;
  created_at: string;
}

export interface Task {
  id: number;
  title: string;
  description?: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  original_image_url?: string;
  processed_image_url?: string;
  metadata?: {
    processing_operation?: string;
    [key: string]: any;
  };
  error_message?: string;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

export interface TaskCreateRequest {
  title: string;
  description?: string;
  processing_operation: string;
}
export interface CreditBalance {
  user_id: number;
  credits: number;
  email: string;
}

export interface CreditPurchaseRequest {
  credits: number;
}

export interface CreditPurchaseResponse {
  order_id: string;
  amount: number;
  currency: string;
  key: string;
}

export interface LoginRequest {
  username: string; // email
  password: string;
  remember_me?: boolean;
}

export interface SignupRequest {
  email: string;
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RefreshTokenRequest {
  refresh_token?: string;
}

export interface SessionInfo {
  session_id: string;
  device_type: string;
  ip_address: string;
  location?: string;
  created_at: string;
  last_activity: string;
  is_remember_me: boolean;
}

export interface SecurityEvent {
  event_type: string;
  severity: string;
  created_at: string;
  ip_address: string;
  success: boolean;
}

export interface SecuritySummary {
  active_sessions: number;
  session_details: SessionInfo[];
  recent_security_events: SecurityEvent[];
}

export interface AdminStats {
  total_users: number;
  total_tasks: number;
  active_users: number;
  admin_users: number;
}