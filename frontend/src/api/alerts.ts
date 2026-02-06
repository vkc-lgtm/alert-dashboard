import { api } from '../lib/api';
import {
  Alert,
  AlertDetail,
  AlertListResponse,
  AlertStats,
  AlertSeverity,
  AlertStatus,
} from '../types';

interface GetAlertsParams {
  page?: number;
  page_size?: number;
  status?: AlertStatus;
  severity?: AlertSeverity;
  source?: string;
  search?: string;
}

export const alertsApi = {
  getAlerts: async (params: GetAlertsParams = {}): Promise<AlertListResponse> => {
    const response = await api.get('/alerts', { params });
    return response.data;
  },

  getAlert: async (id: number): Promise<AlertDetail> => {
    const response = await api.get(`/alerts/${id}`);
    return response.data;
  },

  getStats: async (): Promise<AlertStats> => {
    const response = await api.get('/alerts/stats');
    return response.data;
  },

  createAlert: async (data: {
    title: string;
    description?: string;
    severity?: AlertSeverity;
  }): Promise<Alert> => {
    const response = await api.post('/alerts', data);
    return response.data;
  },

  acknowledgeAlert: async (id: number, comment?: string): Promise<Alert> => {
    const response = await api.post(`/alerts/${id}/acknowledge`, { comment });
    return response.data;
  },

  resolveAlert: async (id: number, comment?: string): Promise<Alert> => {
    const response = await api.post(`/alerts/${id}/resolve`, { comment });
    return response.data;
  },
};
