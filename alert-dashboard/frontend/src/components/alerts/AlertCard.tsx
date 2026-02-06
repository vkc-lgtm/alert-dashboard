import React from 'react';
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { AlertSeverity, AlertStatus, Alert } from '../../types';
import { formatDistanceToNow } from 'date-fns';

interface AlertCardProps {
  alert: Alert;
  onClick?: () => void;
  onAcknowledge?: () => void;
  onResolve?: () => void;
}

const severityConfig: Record<AlertSeverity, { icon: React.ElementType; className: string }> = {
  critical: {
    icon: XCircle,
    className: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800',
  },
  warning: {
    icon: AlertCircle,
    className: 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800',
  },
  info: {
    icon: Info,
    className: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800',
  },
};

const statusColors: Record<AlertStatus, string> = {
  firing: 'bg-red-500',
  acknowledged: 'bg-yellow-500',
  resolved: 'bg-green-500',
};

export function AlertCard({ alert, onClick, onAcknowledge, onResolve }: AlertCardProps) {
  const severity = severityConfig[alert.severity];
  const SeverityIcon = severity.icon;

  return (
    <div
      className={clsx(
        'border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md',
        severity.className
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <SeverityIcon className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span
                className={clsx(
                  'w-2 h-2 rounded-full flex-shrink-0',
                  statusColors[alert.status]
                )}
              />
              <span className="text-xs font-medium uppercase">
                {alert.status}
              </span>
              <span className="text-xs opacity-70">
                • {alert.source}
              </span>
            </div>
            <h3 className="font-semibold truncate">{alert.title}</h3>
            {alert.description && (
              <p className="text-sm opacity-80 mt-1 line-clamp-2">
                {alert.description}
              </p>
            )}
            <p className="text-xs opacity-60 mt-2">
              Fired {formatDistanceToNow(new Date(alert.fired_at), { addSuffix: true })}
            </p>
          </div>
        </div>
        
        {alert.status !== 'resolved' && (
          <div className="flex gap-2 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
            {alert.status === 'firing' && onAcknowledge && (
              <button
                onClick={onAcknowledge}
                className="px-3 py-1 text-xs font-medium bg-yellow-500 text-white rounded hover:bg-yellow-600 transition-colors"
              >
                Ack
              </button>
            )}
            {onResolve && (
              <button
                onClick={onResolve}
                className="px-3 py-1 text-xs font-medium bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
              >
                Resolve
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
