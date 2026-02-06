import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertsApi } from '../api/alerts';
import { AlertSeverity, AlertStatus } from '../types';

interface UseAlertsParams {
  page?: number;
  pageSize?: number;
  status?: AlertStatus;
  severity?: AlertSeverity;
  search?: string;
}

export function useAlerts(params: UseAlertsParams = {}) {
  return useQuery({
    queryKey: ['alerts', params],
    queryFn: () => alertsApi.getAlerts({
      page: params.page || 1,
      page_size: params.pageSize || 50,
      status: params.status,
      severity: params.severity,
      search: params.search,
    }),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useAlert(id: number) {
  return useQuery({
    queryKey: ['alert', id],
    queryFn: () => alertsApi.getAlert(id),
    enabled: !!id,
  });
}

export function useAlertStats() {
  return useQuery({
    queryKey: ['alertStats'],
    queryFn: alertsApi.getStats,
    refetchInterval: 30000,
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, comment }: { id: number; comment?: string }) =>
      alertsApi.acknowledgeAlert(id, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alertStats'] });
    },
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, comment }: { id: number; comment?: string }) =>
      alertsApi.resolveAlert(id, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alertStats'] });
    },
  });
}

export function useCreateAlert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: alertsApi.createAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alertStats'] });
    },
  });
}
