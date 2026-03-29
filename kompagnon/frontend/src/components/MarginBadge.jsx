import React from 'react';

export default function MarginBadge({ marginPercent, status = 'green' }) {
  const statusColors = {
    green: 'bg-success text-white',
    yellow: 'bg-warning text-white',
    red: 'bg-danger text-white',
  };

  const statusIcons = {
    green: '✓',
    yellow: '⚠',
    red: '✗',
  };

  const bgColor = statusColors[status] || statusColors.green;
  const icon = statusIcons[status] || '✓';

  return (
    <span className={`inline-block px-3 py-1 rounded-full font-bold text-sm ${bgColor}`}>
      {marginPercent?.toFixed(1)}% {icon}
    </span>
  );
}
