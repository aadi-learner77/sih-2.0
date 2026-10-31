import React from 'react';

/**
 * Reusable accessible loading spinner
 */
export default function Spinner({ 
  size = 'md', 
  className = '', 
  label = 'Loading...',
  color = 'currentColor'
}) {
  const sizeMap = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-10 h-10 border-3',
    xl: 'w-14 h-14 border-4',
  };

  const dimClass = sizeMap[size] || sizeMap.md;

  return (
    <div 
      role="status" 
      aria-label={label}
      className={`inline-flex items-center justify-center ${className}`}
    >
      <div 
        className={`${dimClass} border-primary/20 border-t-primary rounded-full animate-spin`}
        style={{ borderTopColor: color !== 'currentColor' ? color : undefined }}
      />
      <span className="sr-only">{label}</span>
    </div>
  );
}

