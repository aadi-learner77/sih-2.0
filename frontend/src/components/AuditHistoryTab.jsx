import React from 'react';
import AuditAndReceiptsPage from '../pages/AuditAndReceiptsPage';

/**
 * AuditHistoryTab component: Re-exports the full Audit and Receipts page
 * with receipts timeline, green chain animation, and demo tamper toggle.
 */
export default function AuditHistoryTab(props) {
  return <AuditAndReceiptsPage {...props} />;
}
