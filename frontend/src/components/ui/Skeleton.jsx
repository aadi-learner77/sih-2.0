import React from 'react';

/**
 * Reusable accessible Skeleton loader
 */
export default function Skeleton({ 
  className = '', 
  variant = 'text', // 'text', 'circular', 'rectangular'
  width, 
  height,
  style = {} 
}) {
  const baseClasses = 'bg-surface-2/80 dark:bg-surface-2/40 animate-pulse border border-border/40';
  
  const variantClasses = {
    text: 'h-4 w-full rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-xl',
  };

  const inlineStyles = {
    ...(width ? { width } : {}),
    ...(height ? { height } : {}),
    ...style,
  };

  return (
    <div 
      className={`${baseClasses} ${variantClasses[variant] || variantClasses.text} ${className}`}
      style={inlineStyles}
      aria-hidden="true"
    />
  );
}
