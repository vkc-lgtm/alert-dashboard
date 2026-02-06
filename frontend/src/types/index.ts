// API Types

export type AlertSeverity = 'critical' | 'warning' | 'info';
export type AlertStatus = 'firing' | 'acknowledged' | 'resolved';
export type UserRole = 'admin' | 'user' | 'viewer';

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  email_notifications: boolean;
  slack_notifications: boolean;
  created_at: string;
  last_login: string | null;
}

export interface Alert {
  id: number;
  fingerprint: string;
  title: string;
  description: string | null;
  severity: AlertSeverity;
  status: AlertStatus;
  source: string;
  labels: Record<string, string> | null;
  annotations: Record<string, string> | null;
  fired_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
  acknowledged_by_id: number | null;
  resolved_by_id: number | null;
}

export interface AlertHistory {
  id: number;
  action: string;
  comment: string | null;
  created_at: string;
  user_id: number | null;
  user_email: string | null;
}

export interface AlertDetail extends Alert {
  history: AlertHistory[];
  acknowledged_by_email: string | null;
  resolved_by_email: string | null;
}

export interface AlertStats {
  total: number;
  firing: number;
  acknowledged: number;
  resolved: number;
  critical: number;
  warning: number;
  info: number;
}

export interface AlertListResponse {
  alerts: Alert[];
  total: number;
  page: number;
  page_size: number;
}

export interface UserListResponse {
  users: User[];
  total: number;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface ApiError {
  detail: string;
}
