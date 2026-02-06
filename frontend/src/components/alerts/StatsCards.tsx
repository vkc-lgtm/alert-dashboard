import { clsx } from 'clsx';
import { AlertStats } from '../../types';
import { AlertCircle, CheckCircle, XCircle, Info, Bell, BellOff } from 'lucide-react';

interface StatsCardsProps {
  stats: AlertStats | undefined;
  isLoading: boolean;
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-4 animate-pulse">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      label: 'Firing',
      value: stats?.firing || 0,
      icon: Bell,
      className: 'text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400',
      iconBg: 'bg-red-100 dark:bg-red-900/40',
    },
    {
      label: 'Acknowledged',
      value: stats?.acknowledged || 0,
      icon: AlertCircle,
      className: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20 dark:text-yellow-400',
      iconBg: 'bg-yellow-100 dark:bg-yellow-900/40',
    },
    {
      label: 'Resolved',
      value: stats?.resolved || 0,
      icon: CheckCircle,
      className: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400',
      iconBg: 'bg-green-100 dark:bg-green-900/40',
    },
    {
      label: 'Critical',
      value: stats?.critical || 0,
      icon: XCircle,
      className: 'text-red-700 bg-red-50 dark:bg-red-900/20 dark:text-red-300',
      iconBg: 'bg-red-100 dark:bg-red-900/40',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.label}
            className={clsx(
              'rounded-lg p-4 border',
              card.className
            )}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-80">{card.label}</p>
                <p className="text-3xl font-bold mt-1">{card.value}</p>
              </div>
              <div className={clsx('p-3 rounded-full', card.iconBg)}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
