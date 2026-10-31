import React, { useEffect, useRef } from 'react';
import { AlertTriangle, AlertCircle, Info, X } from 'lucide-react';

/**
 * Reusable accessible Confirmation Modal
 * Implements focus trap, Esc to close, backdrop overlay click, aria-modal and aria-labelledby.
 */
export default function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirm Action',
  description = 'Are you sure you wish to proceed with this action?',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger', // 'danger' | 'warning' | 'primary'
  confirmLoading = false
}) {
  const modalRef = useRef(null);
  const confirmBtnRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;

    // Focus initial confirm button
    const timer = setTimeout(() => {
      confirmBtnRef.current?.focus();
    }, 50);

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }

      // Focus trap
      if (e.key === 'Tab' && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const iconMap = {
    danger: <AlertTriangle className="w-5 h-5 text-rose-500" />,
    warning: <AlertCircle className="w-5 h-5 text-amber-500" />,
    primary: <Info className="w-5 h-5 text-primary" />,
  };

  const confirmBtnStyles = {
    danger: 'bg-rose-600 hover:bg-rose-700 text-white shadow-xs',
    warning: 'bg-amber-600 hover:bg-amber-700 text-white shadow-xs',
    primary: 'bg-primary hover:bg-primary-hover text-white shadow-xs',
  };

  return (
    <div 
      className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fadeIn"
      onClick={onClose}
      aria-hidden="true"
    >
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-modal-title"
        aria-describedby="confirm-modal-desc"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md bg-surface border border-border rounded-2xl shadow-2xl overflow-hidden animate-scaleUp text-text"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border bg-surface-2/60">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-surface border border-border">
              {iconMap[variant] || iconMap.primary}
            </div>
            <h3 id="confirm-modal-title" className="text-sm font-bold text-text">
              {title}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-text-muted hover:text-text hover:bg-surface-2 transition-colors cursor-pointer"
            aria-label="Close dialog"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4">
          <p id="confirm-modal-desc" className="text-xs text-text-muted leading-relaxed">
            {description}
          </p>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-2 px-5 py-3.5 bg-surface-2/60 border-t border-border">
          <button
            type="button"
            onClick={onClose}
            disabled={confirmLoading}
            className="px-3.5 py-1.5 rounded-lg border border-border bg-surface text-text text-xs font-semibold hover:bg-surface-2 transition-colors cursor-pointer"
          >
            {cancelText}
          </button>
          <button
            ref={confirmBtnRef}
            type="button"
            onClick={onConfirm}
            disabled={confirmLoading}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${confirmBtnStyles[variant] || confirmBtnStyles.primary}`}
          >
            {confirmLoading ? 'Processing...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

