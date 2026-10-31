import React from 'react';
import { Clock } from 'lucide-react';
import { LAST_UPDATED } from '../../config';

/**
 * Reusable LastUpdated component displaying system / regulatory revision timestamp
 */
export default function LastUpdated({ 
  date = LAST_UPDATED, 
  prefix = 'Last updated:', 
  className = '' 
}) {
  const displayDate = (() => {
    try {
      const d = new Date(date);
      if (isNaN(d.getTime())) return date;
      return d.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return date;
    }
  })();

  return (
    <div className={`inline-flex items-center gap-1.5 text-xs text-text-muted ${className}`}>
      <Clock className="w-3.5 h-3.5 text-text-subtle shrink-0" aria-hidden="true" />
      <span>{prefix}</span>
      <time dateTime={date} className="font-medium text-text">
        {displayDate}
      </time>
    </div>
  );
}

