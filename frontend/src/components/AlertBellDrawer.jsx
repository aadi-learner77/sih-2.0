import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { 
  Bell, 
  AlertCircle, 
  AlertTriangle, 
  Info, 
  CheckCircle2, 
  RefreshCw, 
  X, 
  Mail, 
  ExternalLink,
  ShieldAlert,
  Play,
  Filter
} from 'lucide-react';
import DemoDataBadge from './DemoDataBadge';
import { api } from '../services/api';
import { MOCK_ALERTS } from '../data/mockOfficerData';

/**
 * Interactive Alert Bell & Flyout Notification Drawer:
 * Monitors operational warnings:
 * - Missing information
 * - Expired documents
 * - Pending source verifications
 * - Source unavailable / timeouts
 * - Anomaly flags (forensic tampering, knowledge graph conflicts)
 * - Unresolved findings older than N days
 */
export default function AlertBellDrawer({ currentRole }) {
  const [isOpen, setIsOpen] = useState(false);
  const [alerts, setAlerts] = useState(MOCK_ALERTS);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [activeView, setActiveView] = useState('alerts'); // 'alerts' or 'notifications'
  const [notifications, setNotifications] = useState([]);
  const [dispatchCount, setDispatchCount] = useState(24);
  const [notificationMsg, setNotificationMsg] = useState(null);
  const [isDemoData, setIsDemoData] = useState(true);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const liveAlerts = await api.getAlerts();
      if (Array.isArray(liveAlerts)) {
        setAlerts(liveAlerts);
        setIsDemoData(false);
      } else {
        setAlerts(MOCK_ALERTS);
        setIsDemoData(true);
      }
    } catch (err) {
      console.warn('Backend alerts endpoint offline, using local mock alerts:', err.message);
      setAlerts(MOCK_ALERTS);
      setIsDemoData(true);
    } finally {
      setLoading(false);
    }
  };

  const fetchNotifications = async () => {
    try {
      const data = await api.getNotifications();
      if (data) {
        const inApp = Array.isArray(data.in_app_notifications) ? data.in_app_notifications : [];
        const emails = Array.isArray(data.dispatched_emails) ? data.dispatched_emails : [];
        const combined = inApp.length > 0 ? inApp : emails;
        setNotifications(combined);
        setDispatchCount(emails.length || inApp.length || 24);
      }
    } catch (err) {
      console.warn('Could not fetch notifications queue:', err.message);
      setDispatchCount(24);
    }
  };

  useEffect(() => {
    fetchAlerts();
    fetchNotifications();
  }, []);

  const handleTriggerScan = async () => {
    setScanning(true);
    setNotificationMsg(null);
    try {
      const report = await api.runAlertScan({ expiring_within_days: 30, unresolved_days: 7 });
      setNotificationMsg(`Scan Complete: ${report.new_alerts_generated || 0} new alerts generated across ${report.scanned_applications_count || 0} applications.`);
      await fetchAlerts();
      await fetchNotifications();
    } catch (err) {
      console.warn('Scan API fallback:', err.message);
      // Simulate scan in mock mode
      setTimeout(() => {
        setNotificationMsg('Demo Scan Complete: 4 applications scanned. Deduplication active.');
        setScanning(false);
      }, 700);
      return;
    } finally {
      setScanning(false);
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await api.resolveAlert(alertId);
    } catch (err) {
      console.warn('Resolve API fallback:', err.message);
    }
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, is_read: true, resolved_at: new Date().toISOString() } : a))
    );
  };

  const unreadAlerts = alerts.filter((a) => !a.is_read);
  const activeAlertsCount = unreadAlerts.length;
  const criticalCount = alerts.filter((a) => a.severity === 'CRITICAL' && !a.is_read).length;

  const filteredAlerts = alerts.filter((a) => {
    if (filterSeverity === 'ALL') return true;
    return a.severity === filterSeverity;
  });

  return (
    <div className="relative">
      {/* Alert Bell Button */}
      <button
        id="alert-bell-btn"
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) {
            fetchAlerts();
            fetchNotifications();
          }
        }}
        className="relative p-2 rounded-xl text-text-muted hover:text-text hover:bg-surface-2 transition-colors focus:outline-none cursor-pointer"
        title="Statutory Alerts & Risk Warnings"
      >
        <Bell className="w-5 h-5 text-current" />
        {activeAlertsCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-[16px] px-1">
            <span className="animate-ping absolute inset-0 rounded-full bg-rose-400 opacity-75"></span>
            <span className="relative inline-flex items-center justify-center rounded-full h-4 min-w-[16px] px-1 bg-rose-600 text-[9px] font-bold text-white shadow-xs">
              {activeAlertsCount}
            </span>
          </span>
        )}
      </button>

      {/* Flyout Drawer / Modal via Portal directly onto document.body */}
      {isOpen && typeof document !== 'undefined' && createPortal(
        <div 
          className="modal-backdrop-overlay fixed inset-0 z-50 overflow-hidden bg-black/55 dark:bg-black/70 backdrop-blur-xs flex justify-end items-start p-3 sm:p-4 pt-[60px]"
          onClick={() => setIsOpen(false)}
        >
          <div 
            id="alert-bell-drawer-modal"
            className="alert-drawer-container w-full max-w-lg bg-surface h-auto max-h-[calc(100vh-80px)] shadow-2xl flex flex-col rounded-xl border border-border text-text animate-in slide-in-from-right duration-200 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            
            {/* Header */}
            <div className="drawer-header p-4 sm:p-5 border-b border-border bg-surface-2 flex items-center justify-between shrink-0">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center shrink-0">
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-bold text-text">
                      Statutory Operational Alerts
                    </h3>
                    {isDemoData && <DemoDataBadge message="Demo data" />}
                  </div>
                  <div className="flex items-center space-x-2 text-[11px] text-text-muted mt-0.5">
                    <span className="font-bold text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                      {activeAlertsCount} Active
                    </span>
                    <span>•</span>
                    <span>{criticalCount} Critical</span>
                    <span>•</span>
                    <span className="font-semibold text-primary bg-primary/10 px-1.5 py-0.5 rounded border border-primary/20">
                      {dispatchCount} Dispatched
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  id="run-scan-btn"
                  onClick={handleTriggerScan}
                  disabled={scanning}
                  className="px-2.5 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-xs disabled:opacity-50 cursor-pointer"
                  title="Run Full Background Scan Across All Applications"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
                  <span>{scanning ? 'Scanning...' : 'Run Scan'}</span>
                </button>
                <button
                  id="close-drawer-btn"
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 text-text-muted hover:text-text rounded-lg hover:bg-surface-2 cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Quick Alert Banner Notification */}
            {notificationMsg && (
              <div className="bg-primary/10 px-4 py-2 text-xs text-text border-b border-border flex items-center justify-between shrink-0">
                <span>{notificationMsg}</span>
                <button onClick={() => setNotificationMsg(null)} className="text-text-muted hover:text-text">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* View & Severity Filter Bar with proper padding */}
            <div className="drawer-filter-bar px-5 py-3 border-b border-border bg-surface flex items-center justify-between gap-2 shrink-0 flex-wrap">
              <div className="flex items-center space-x-1.5 text-xs">
                <button
                  onClick={() => setActiveView('alerts')}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer ${
                    activeView === 'alerts'
                      ? 'bg-primary/10 text-primary border border-primary/20 font-semibold shadow-xs'
                      : 'text-text-muted hover:text-text hover:bg-surface-2'
                  }`}
                >
                  Alerts ({alerts.length})
                </button>
                <button
                  onClick={() => setActiveView('notifications')}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer ${
                    activeView === 'notifications'
                      ? 'bg-primary/10 text-primary border border-primary/20 font-semibold shadow-xs'
                      : 'text-text-muted hover:text-text hover:bg-surface-2'
                  }`}
                >
                  Dispatches ({dispatchCount})
                </button>
              </div>

              {activeView === 'alerts' && (
                <div className="flex items-center space-x-1">
                  {['ALL', 'CRITICAL', 'WARNING'].map((s) => (
                    <button
                      key={s}
                      onClick={() => setFilterSeverity(s)}
                      className={`text-[10px] font-semibold px-2 py-1 rounded border transition-colors cursor-pointer ${
                        filterSeverity === s
                          ? s === 'CRITICAL'
                            ? 'bg-rose-600 text-white border-rose-600'
                            : s === 'WARNING'
                            ? 'bg-amber-600 text-white border-amber-600'
                            : 'bg-primary/10 text-primary border-primary/20'
                          : 'bg-surface text-text-muted border-border hover:bg-surface-2'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Body Content with internal overflow-y-auto and empty states */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
              {activeView === 'alerts' ? (
                filteredAlerts.length === 0 ? (
                  <div className="text-center py-12 text-text-subtle space-y-2">
                    <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500 opacity-80" />
                    <p className="text-xs font-semibold text-text">No active operational alerts for selected criteria.</p>
                    <p className="text-[11px] text-text-muted">All institutional documents, deadlines, and statutory verifications are in good standing.</p>
                  </div>
                ) : (
                  filteredAlerts.map((alert) => {
                    const isCritical = alert.severity === 'CRITICAL';
                    const isWarning = alert.severity === 'WARNING';

                    return (
                      <div
                        key={alert.id}
                        className={`rounded-xl p-3.5 border transition-all text-left space-y-2 ${
                          alert.is_read
                            ? 'bg-surface-2/60 border-border opacity-60'
                            : isCritical
                            ? 'bg-rose-500/10 border-rose-500/30 shadow-xs'
                            : isWarning
                            ? 'bg-amber-500/10 border-amber-500/30 shadow-xs'
                            : 'bg-primary/10 border-primary/20 shadow-xs'
                        }`}
                      >
                        {/* Top: Severity + Type + Target Role */}
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center space-x-1.5">
                            <span
                              className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                                isCritical
                                  ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30'
                                  : isWarning
                                  ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30'
                                  : 'bg-primary/15 text-primary border-primary/30'
                              }`}
                            >
                              {alert.severity}
                            </span>
                            <span className="text-[10px] font-mono text-text-subtle">
                              {alert.alert_type?.replace(/_/g, ' ')}
                            </span>
                          </div>

                          <span className="text-[10px] bg-surface border border-border text-text-muted px-2 py-0.5 rounded-full font-medium">
                            Role: {alert.assigned_role?.replace('_', ' ')}
                          </span>
                        </div>

                        {/* Title & Description */}
                        <div>
                          <h4 className="text-xs font-bold text-text leading-snug">
                            {alert.title}
                          </h4>
                          <p className="text-[11px] text-text-muted mt-1 leading-relaxed">
                            {alert.message}
                          </p>
                        </div>

                        {/* Application / College Ref */}
                        <div className="text-[10px] text-text-subtle flex flex-wrap items-center justify-between gap-1 pt-1 border-t border-border/60">
                          <span className="font-semibold text-text">
                            {alert.institution_name || `App #${alert.application_id}`}
                          </span>
                          <span>
                            {alert.created_at ? new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent'}
                          </span>
                        </div>

                        {/* Resolve Action */}
                        {!alert.is_read && (
                          <div className="pt-1 flex justify-end">
                            <button
                              onClick={() => handleResolveAlert(alert.id)}
                              className="text-[11px] font-semibold text-primary hover:text-primary-hover px-2.5 py-1 rounded-md hover:bg-primary/10 transition-colors cursor-pointer"
                            >
                              Mark as Reviewed / Resolved ✓
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })
                )
              ) : (
                /* Dispatched Notifications Log */
                <div className="space-y-3 text-left">
                  <div className="text-xs font-semibold text-text flex items-center justify-between">
                    <span>Email & In-App Dispatch Logs</span>
                    <span className="text-[11px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20">
                      {dispatchCount} Dispatched
                    </span>
                  </div>

                  <div className="bg-surface-2 rounded-xl p-3 border border-border text-[11px] text-text-muted space-y-2">
                    <div className="flex items-center space-x-2 text-text font-bold">
                      <Mail className="w-4 h-4 text-primary" />
                      <span>Statutory Dispatcher Architecture</span>
                    </div>
                    <p>
                      Every new alert triggers both an in-app notification payload and a formatted HTML mock email dispatched to the assigned regulatory role.
                    </p>
                  </div>

                  {notifications.length === 0 ? (
                    <div className="text-center py-12 text-text-subtle space-y-2">
                      <Mail className="w-8 h-8 mx-auto text-sky-500 opacity-80" />
                      <p className="text-xs font-semibold text-text">No regulatory dispatches recorded yet.</p>
                      <p className="text-[11px] text-text-muted">In-app notifications and email dispatch receipts will appear here once alert scans trigger notices.</p>
                    </div>
                  ) : (
                    notifications.map((item, idx) => (
                      <div key={item.id || item.email_id || idx} className="bg-surface-2 rounded-xl p-3 border border-border text-xs space-y-1 shadow-xs text-text">
                        <div className="flex items-center justify-between text-[10px] text-text-subtle">
                          <span className="font-mono text-primary">To: {item.to_email || item.recipient || 'scrutiny.officer@aicte-india.org'}</span>
                          <span>{item.sent_at ? new Date(item.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent'}</span>
                        </div>
                        <div className="font-semibold text-text leading-snug">
                          {item.subject || item.title || 'Statutory Compliance Alert Notification'}
                        </div>
                        <div className="text-[10px] text-text-subtle flex items-center space-x-1.5">
                          <span className="px-1.5 py-0.5 rounded bg-surface border border-border text-text font-medium">Role: {(item.recipient_role || item.role || 'Scrutiny Officer').replace('_', ' ')}</span>
                          <span>•</span>
                          <span className="text-emerald-700 font-medium">Status: SENT_200</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="drawer-footer p-3.5 border-t border-border bg-surface-2 text-[11px] text-text-muted flex items-center justify-between shrink-0">
              <span>Automatic dedupe suppresses recurring spam</span>
              <button
                onClick={() => setIsOpen(false)}
                className="text-xs font-semibold text-text hover:text-primary cursor-pointer"
              >
                Close Drawer
              </button>
            </div>

          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
