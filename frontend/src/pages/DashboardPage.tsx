import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAlerts, useAlertStats, useAcknowledgeAlert, useResolveAlert } from '../../hooks/useAlerts';
import { useWebSocket } from '../../hooks/useWebSocket';
import { AlertCard } from '../../components/alerts/AlertCard';
import { StatsCards } from '../../components/alerts/StatsCards';
import { AlertFilters } from '../../components/alerts/AlertFilters';
import { AlertSeverity, AlertStatus } from '../../types';
import { RefreshCw } from 'lucide-react';

export function DashboardPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<{
    status?: AlertStatus;
    severity?: AlertSeverity;
    search?: string;
  }>({});
  const [page, setPage] = useState(1);

  // Connect to WebSocket for real-time updates
  useWebSocket();

  const { data: alertsData, isLoading: alertsLoading, refetch } = useAlerts({
    page,
    pageSize: 50,
    ...filters,
  });

  const { data: stats, isLoading: statsLoading } = useAlertStats();
  const acknowledgeMutation = useAcknowledgeAlert();
  const resolveMutation = useResolveAlert();

  const handleFilterChange = useCallback((newFilters: typeof filters) => {
    setFilters(newFilters);
    setPage(1);
  }, []);

  const handleAcknowledge = async (alertId: number) => {
    try {
      await acknowledgeMutation.mutateAsync({ id: alertId });
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const handleResolve = async (alertId: number) => {
    try {
      await resolveMutation.mutateAsync({ id: alertId });
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Alert Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Monitor and manage alerts from your infrastructure
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <StatsCards stats={stats} isLoading={statsLoading} />

      {/* Filters */}
      <AlertFilters onFilterChange={handleFilterChange} />

      {/* Alerts List */}
      <div className="space-y-3">
        {alertsLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="bg-white dark:bg-gray-800 rounded-lg p-4 animate-pulse"
              >
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : alertsData?.alerts.length === 0 ? (
          <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400">
              No alerts found matching your criteria
            </p>
          </div>
        ) : (
          alertsData?.alerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onClick={() => navigate(`/alerts/${alert.id}`)}
              onAcknowledge={() => handleAcknowledge(alert.id)}
              onResolve={() => handleResolve(alert.id)}
            />
          ))
        )}
      </div>

      {/* Pagination */}
      {alertsData && alertsData.total > alertsData.page_size && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-gray-600 dark:text-gray-400">
            Page {page} of {Math.ceil(alertsData.total / alertsData.page_size)}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= Math.ceil(alertsData.total / alertsData.page_size)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
