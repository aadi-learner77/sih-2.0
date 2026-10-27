import React, { useState, useEffect } from 'react';
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
  const [notificationMsg, setNotificationMsg] = useState(null);
  const [isDemoData, setIsDemoData] = useState(true);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const liveAlerts = await api.getAlerts();
      if (liveAlerts && Array.isArray(liveAlerts)) {
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
        setNotifications(data.in_app_notifications || []);
      }
    } catch (err) {
      console.warn('Could not fetch notifications queue:', err.message);
    }
  };

  useEffect(() => {
    fetchAlerts();
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
        className="relative p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors focus:outline-none cursor-pointer"
        title="Statutory Alerts & Risk Warnings"
      >
        <Bell className="w-5 h-5" />
        {unreadAlerts.length > 0 && (
          <span className="absolute top-1 right-1 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
            <span className="relative inline-flex items-center justify-center rounded-full h-4 w-4 bg-rose-600 text-[9px] font-bold text-white">
              {unreadAlerts.length}
            </span>
          </span>
        )}
      </button>

      {/* Flyout Drawer / Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-[rgba(0,0,0,0.15)] backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-lg bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 animate-in slide-in-from-right duration-200">
            
            {/* Header */}
            <div className="p-4 sm:p-5 border-b border-slate-200 bg-slate-50/70 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center">
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-bold text-slate-900">
                      Statutory Operational Alerts
                    </h3>
                    {isDemoData && <DemoDataBadge message="Demo data" />}
                  </div>
                  <p className="text-[11px] text-slate-500">
                    {unreadAlerts.length} Active • {criticalCount} Critical Flags
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  id="run-scan-btn"
                  onClick={handleTriggerScan}
                  disabled={scanning}
                  className="px-2.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-xs disabled:opacity-50 cursor-pointer"
                  title="Run Full Background Scan Across All Applications"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
                  <span>{scanning ? 'Scanning...' : 'Run Scan'}</span>
                </button>
                <button
                  id="close-drawer-btn"
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/60 cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Quick Alert Banner Notification */}
            {notificationMsg && (
              <div className="bg-sky-50 px-4 py-2 text-xs text-sky-800 border-b border-sky-200 flex items-center justify-between">
                <span>{notificationMsg}</span>
                <button onClick={() => setNotificationMsg(null)} className="text-sky-600 hover:text-sky-900">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* View & Severity Filter Bar */}
            <div className="px-4 py-2.5 border-b border-slate-200 bg-white flex items-center justify-between gap-2">
              <div className="flex items-center space-x-1 text-xs">
                <button
                  onClick={() => setActiveView('alerts')}
                  className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                    activeView === 'alerts'
                      ? 'bg-[#E8F1FB] text-[#000000] border border-[#BBD4F0] font-semibold shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  Alerts ({alerts.length})
                </button>
                <button
                  onClick={() => setActiveView('notifications')}
                  className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                    activeView === 'notifications'
                      ? 'bg-[#E8F1FB] text-[#000000] border border-[#BBD4F0] font-semibold shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  Dispatches (In-App/Email)
                </button>
              </div>

              {activeView === 'alerts' && (
                <div className="flex items-center space-x-1">
                  {['ALL', 'CRITICAL', 'WARNING'].map((s) => (
                    <button
                      key={s}
                      onClick={() => setFilterSeverity(s)}
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded border transition-colors ${
                        filterSeverity === s
                          ? s === 'CRITICAL'
                            ? 'bg-rose-600 text-white border-rose-600'
                            : s === 'WARNING'
                            ? 'bg-amber-600 text-white border-amber-600'
                            : 'bg-[#E8F1FB] text-[#000000] border-[#BBD4F0]'
                          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Body Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {activeView === 'alerts' ? (
                filteredAlerts.length === 0 ? (
                  <div className="text-center py-12 text-slate-400 space-y-2">
                    <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500 opacity-80" />
                    <p className="text-xs">No active operational alerts for selected criteria.</p>
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
                            ? 'bg-slate-50/60 border-slate-200 opacity-60'
                            : isCritical
                            ? 'bg-rose-50/40 border-rose-200/90 shadow-xs'
                            : isWarning
                            ? 'bg-amber-50/40 border-amber-200/90 shadow-xs'
                            : 'bg-sky-50/30 border-sky-200/90 shadow-xs'
                        }`}
                      >
                        {/* Top: Severity + Type + Target Role */}
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center space-x-1.5">
                            <span
                              className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                                isCritical
                                  ? 'bg-rose-100 text-rose-800 border-rose-200'
                                  : isWarning
                                  ? 'bg-amber-100 text-amber-800 border-amber-200'
                                  : 'bg-sky-100 text-sky-800 border-sky-200'
                              }`}
                            >
                              {alert.severity}
                            </span>
                            <span className="text-[10px] font-mono text-slate-500">
                              {alert.alert_type?.replace(/_/g, ' ')}
                            </span>
                          </div>

                          <span className="text-[10px] bg-white border border-slate-200 text-slate-600 px-2 py-0.5 rounded-full font-medium">
                            Role: {alert.assigned_role?.replace('_', ' ')}
                          </span>
                        </div>

                        {/* Title & Description */}
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 leading-snug">
                            {alert.title}
                          </h4>
                          <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                            {alert.message}
                          </p>
                        </div>

                        {/* Application / College Ref */}
                        <div className="text-[10px] text-slate-500 flex flex-wrap items-center justify-between gap-1 pt-1 border-t border-slate-200/60">
                          <span className="font-semibold text-slate-700">
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
                              className="text-[11px] font-semibold text-sky-700 hover:text-sky-900 px-2.5 py-1 rounded-md hover:bg-sky-100/60 transition-colors"
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
                  <div className="text-xs font-semibold text-slate-700 flex items-center justify-between">
                    <span>Mock Email & In-App Dispatch Logs</span>
                    <span className="text-[11px] text-slate-500">{notifications.length || 4} Dispatched</span>
                  </div>

                  <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 text-[11px] text-slate-600 space-y-2">
                    <div className="flex items-center space-x-2 text-slate-800 font-bold">
                      <Mail className="w-4 h-4 text-sky-600" />
                      <span>Mock Dispatcher Architecture</span>
                    </div>
                    <p>
                      Every new alert triggers both an in-app notification payload and a formatted HTML mock email dispatched to the assigned regulatory role.
                    </p>
                  </div>

                  {/* Sample Mock Email Logs */}
                  {[
                    {
                      to: 'scrutiny.officer@aicte-india.org',
                      role: 'Scrutiny Officer',
                      subject: '[CRITICAL] Expired Statutory Document: Fire Safety Certificate - APP-2025-04421',
                      time: '12m ago',
                    },
                    {
                      to: 'admin@aicte-india.org',
                      role: 'System Admin',
                      subject: '[CRITICAL] Statutory Gateway Unavailable: State Bhoomi Registry - APP-2025-07739',
                      time: '34m ago',
                    },
                    {
                      to: 'senior.officer@aicte-india.org',
                      role: 'Senior Officer',
                      subject: '[CRITICAL] Unresolved Finding (18 Days Old): Faculty Cadre Ratio - APP-2025-09812',
                      time: '1h ago',
                    },
                  ].map((email, idx) => (
                    <div key={idx} className="bg-white rounded-xl p-3 border border-slate-200 text-xs space-y-1 shadow-xs">
                      <div className="flex items-center justify-between text-[10px] text-slate-500">
                        <span className="font-mono text-sky-700">To: {email.to}</span>
                        <span>{email.time}</span>
                      </div>
                      <div className="font-semibold text-slate-900 leading-snug">
                        {email.subject}
                      </div>
                      <div className="text-[10px] text-slate-500 flex items-center space-x-1.5">
                        <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">Role: {email.role}</span>
                        <span>•</span>
                        <span className="text-emerald-700 font-medium">Status: MOCK_SENT_200</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-slate-200 bg-slate-50 text-[11px] text-slate-500 flex items-center justify-between">
              <span>Automatic dedupe suppresses recurring spam</span>
              <button
                onClick={() => setIsOpen(false)}
                className="text-xs font-semibold text-slate-700 hover:text-slate-900"
              >
                Close Drawer
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
