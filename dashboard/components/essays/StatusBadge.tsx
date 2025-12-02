"use client";

import { EssayStatus } from '@/lib/essays/types';
import { getStatusLabel } from '@/lib/essays/utils';
import { FileText } from 'lucide-react';

interface StatusBadgeProps {
  status: EssayStatus;
  showIcon?: boolean;
}

export default function StatusBadge({ status, showIcon = true }: StatusBadgeProps) {
  const getStatusStyles = () => {
    switch (status) {
      case 'not_started':
        return 'bg-gray-600 text-gray-300';
      case 'in_progress':
        return 'bg-blue-600 text-white';
      case 'complete':
        return 'bg-green-600 text-white';
      default:
        return 'bg-gray-600 text-gray-300';
    }
  };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg text-sm font-medium ${getStatusStyles()}`}>
      {showIcon && <FileText size={14} />}
      <span>{getStatusLabel(status)}</span>
    </div>
  );
}

