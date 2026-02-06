import { useState } from 'react';
import { AlertStatus, AlertSeverity } from '../../types';
import { Search, Filter, X } from 'lucide-react';

interface AlertFiltersProps {
  onFilterChange: (filters: {
    status?: AlertStatus;
    severity?: AlertSeverity;
    search?: string;
  }) => void;
}

export function AlertFilters({ onFilterChange }: AlertFiltersProps) {
  const [status, setStatus] = useState<AlertStatus | ''>('');
  const [severity, setSeverity] = useState<AlertSeverity | ''>('');
  const [search, setSearch] = useState('');

  const handleStatusChange = (value: AlertStatus | '') => {
    setStatus(value);
    onFilterChange({
      status: value || undefined,
      severity: severity || undefined,
      search: search || undefined,
    });
  };

  const handleSeverityChange = (value: AlertSeverity | '') => {
    setSeverity(value);
    onFilterChange({
      status: status || undefined,
      severity: value || undefined,
      search: search || undefined,
    });
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    onFilterChange({
      status: status || undefined,
      severity: severity || undefined,
      search: value || undefined,
    });
  };

  const clearFilters = () => {
    setStatus('');
    setSeverity('');
    setSearch('');
    onFilterChange({});
  };

  const hasFilters = status || severity || search;

  return (
    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
      <div className="relative flex-1 w-full sm:max-w-xs">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search alerts..."
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>
      
      <div className="flex gap-2 flex-wrap">
        <select
          value={status}
          onChange={(e) => handleStatusChange(e.target.value as AlertStatus | '')}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Statuses</option>
          <option value="firing">Firing</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>
        
        <select
          value={severity}
          onChange={(e) => handleSeverityChange(e.target.value as AlertSeverity | '')}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>
        
        {hasFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
          >
            <X className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
