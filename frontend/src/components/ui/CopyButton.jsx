import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

/**
 * Reusable accessible CopyButton with clipboard fallback and visual "Copied" state
 */
export default function CopyButton({
  text = '',
  label = 'Copy',
  copiedLabel = 'Copied',
  title = 'Copy to clipboard',
  className = '',
  iconClassName = 'w-3.5 h-3.5',
  showLabel = true,
  children
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e) => {
    e.stopPropagation();
    if (!text) return;

    let success = false;
    if (typeof navigator !== 'undefined' && navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        success = true;
      } catch (err) {
        console.warn('Clipboard writeText failed, using fallback:', err);
      }
    }

    if (!success) {
      // Fallback for non-secure contexts or older browsers
      try {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        success = document.execCommand('copy');
        document.body.removeChild(textarea);
      } catch (fallbackErr) {
        console.error('Fallback copy command failed:', fallbackErr);
      }
    }

    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      title={copied ? copiedLabel : title}
      aria-label={copied ? copiedLabel : title}
      className={`inline-flex items-center gap-1.5 transition-colors cursor-pointer select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
        copied 
          ? 'text-emerald-600 dark:text-emerald-400 font-semibold' 
          : 'text-text-muted hover:text-text'
      } ${className}`}
    >
      {copied ? (
        <Check className={`${iconClassName} text-emerald-500`} />
      ) : (
        <Copy className={iconClassName} />
      )}
      {children ? children(copied) : (
        showLabel && (
          <span className="text-xs transition-opacity duration-150">
            {copied ? copiedLabel : label}
          </span>
        )
      )}
      <span className="sr-only" aria-live="polite">
        {copied ? copiedLabel : ''}
      </span>
    </button>
  );
}

