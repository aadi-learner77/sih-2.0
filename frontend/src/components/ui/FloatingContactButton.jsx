import React from 'react';
import { Mail } from 'lucide-react';
import { CONTACT_EMAIL } from '../../config';

/**
 * FloatingContactButton - Accessible floating help/contact mailto trigger
 * Stacked neatly above bottom-right coordinates so it never overlaps with back-to-top.
 */
export default function FloatingContactButton() {
  return (
    <a
      id="floating-contact-btn"
      href={`mailto:${CONTACT_EMAIL}?subject=PRAMAAN-X%20Regulatory%20Support%20Inquiry`}
      title={`Contact Regulatory Support (${CONTACT_EMAIL})`}
      aria-label="Contact Regulatory Support"
      className="fixed bottom-4 right-4 sm:right-6 z-40 w-10 h-10 rounded-full glass-surface border border-border flex items-center justify-center text-text hover:text-primary transition-all duration-200 cursor-pointer shadow-lg outline-none focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      <Mail className="w-4 h-4" />
    </a>
  );
}

