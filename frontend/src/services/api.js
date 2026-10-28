import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to every outgoing request
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('pramaan_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept 401 Unauthorized responses to redirect to login
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const isLoginRequest = error.config?.url?.includes('/auth/login');
      if (!isLoginRequest) {
        localStorage.removeItem('pramaan_token');
        localStorage.removeItem('pramaan_user');
        window.dispatchEvent(new CustomEvent('pramaan_unauthorized', { detail: error.response.data }));
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Auth
  login: async (email, password) => {
    const res = await apiClient.post('/auth/login', { email, password });
    return res.data;
  },
  getMe: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },

  // Applications
  getApplications: async (category, status) => {
    const res = await apiClient.get('/applications', { params: { category, status } });
    return res.data;
  },
  getApplicationDetail: async (id) => {
    const res = await apiClient.get(`/applications/${id}`);
    return res.data;
  },
  getChecklist: async (id) => {
    const res = await apiClient.get(`/applications/${id}/checklist`);
    return res.data;
  },
  getEvidenceLens: async (id) => {
    const res = await apiClient.get(`/applications/${id}/evidence-lens`);
    return res.data;
  },
  validateApplication: async (id) => {
    const res = await apiClient.post(`/applications/${id}/validate`);
    return res.data;
  },
  getAllFindings: async (severity, status) => {
    const res = await apiClient.get('/applications/findings/all', { params: { severity, status } });
    return res.data;
  },

  // Documents & OCR
  uploadDocument: async (applicationId, file, docType) => {
    const formData = new FormData();
    formData.append('application_id', applicationId);
    formData.append('file', file);
    if (docType) formData.append('document_type', docType);
    const res = await apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  ingestDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/documents/ingest', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  // Regulation-as-Code
  getRules: async () => {
    const res = await apiClient.get('/rules');
    return res.data;
  },
  updateRule: async (ruleId, updatedData) => {
    const res = await apiClient.put(`/rules/${ruleId}`, updatedData);
    return res.data;
  },
  evaluateRules: async (appId) => {
    const res = await apiClient.post(`/rules/evaluate/${appId}`);
    return res.data;
  },
  updateOfficerDecision: async (evalId, decision, comment) => {
    const res = await apiClient.patch(`/rules/evaluations/${evalId}/decision`, { decision, comment });
    return res.data;
  },
  executeWhatIfDryRun: async (payload) => {
    const res = await apiClient.post('/rules/dry-run', payload);
    return res.data;
  },

  // Knowledge Graph & Impossibility Engine
  getKnowledgeGraph: async () => {
    const res = await apiClient.get('/graph');
    return res.data;
  },
  getImpossibilities: async (instId) => {
    const res = await apiClient.get('/graph/impossibilities', { params: { institution_id: instId } });
    return res.data;
  },

  // Forensics & Photo Radar
  scanPhotoRadar: async (phash, instId) => {
    const formData = new FormData();
    formData.append('phash', phash);
    formData.append('institution_id', instId || 'INST_001');
    const res = await apiClient.post('/forensics/photo-radar/scan', formData);
    return res.data;
  },
  getPhotoRegistry: async () => {
    const res = await apiClient.get('/forensics/photo-radar/registry');
    return res.data;
  },
  runELA: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/forensics/ela', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  // Mock Issuer Verification
  queryIssuer: async (applicationId, issuerType, params, docId = null) => {
    const res = await apiClient.post('/verification/query', {
      application_id: applicationId,
      issuer_type: issuerType,
      parameters: params,
      document_id: docId,
    });
    return res.data;
  },

  // Audit Ledger & Logs
  getAuditReceipts: async (appId) => {
    const res = await apiClient.get('/audit/receipts', { params: { application_id: appId } });
    return res.data;
  },
  verifyAuditChain: async (appId) => {
    const res = await apiClient.get('/audit/verify-chain', { params: { application_id: appId } });
    return res.data;
  },
  simulateTampering: async (receiptIndex) => {
    const res = await apiClient.post('/audit/simulate-tamper-demo', null, {
      params: { receipt_index: receiptIndex },
    });
    return res.data;
  },
  restoreTamperDemo: async () => {
    const res = await apiClient.post('/audit/restore-tamper-demo');
    return res.data;
  },
  getAuditLogs: async (limit = 50, action = null) => {
    const res = await apiClient.get('/audit/logs', { params: { limit, action } });
    return res.data;
  },

  // Operational Alerts & Periodic Scanner
  getAlerts: async (params = {}) => {
    const res = await apiClient.get('/alerts', { params });
    return res.data;
  },
  resolveAlert: async (alertId) => {
    const res = await apiClient.patch(`/alerts/${alertId}/resolve`);
    return res.data;
  },
  runAlertScan: async (params = {}) => {
    const res = await apiClient.post('/alerts/run-scan', null, { params });
    return res.data;
  },
  getNotifications: async (params = {}) => {
    const res = await apiClient.get('/alerts/notifications', { params });
    return res.data;
  },
  getSchedulerStatus: async () => {
    const res = await apiClient.get('/alerts/scheduler/status');
    return res.data;
  },

  // Officer Actions & Decisions Log
  performOfficerAction: async (appId, actionData) => {
    const res = await apiClient.post(`/applications/${appId}/officer-action`, actionData);
    return res.data;
  },
  getOfficerActions: async (appId = null) => {
    const url = appId ? `/applications/${appId}/officer-actions` : '/applications/officer-actions/all';
    const res = await apiClient.get(url);
    return res.data;
  },

  // Rectification Flow
  rectifyFinding: async (appId, findingId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post(`/applications/${appId}/findings/${findingId}/rectify`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  // Manual Review Queue & Connector Verification
  getManualReviewQueue: async (status = null, priority = null) => {
    const params = {};
    if (status) params.status = status;
    if (priority) params.priority = priority;
    const res = await apiClient.get('/verification/connector/manual-review-queue', { params });
    return res.data;
  },
  resolveManualReviewItem: async (itemId, resolution, notes, officerEmail = 'senior.officer@aicte.gov.in') => {
    const res = await apiClient.post(`/verification/connector/manual-review-queue/${itemId}/resolve`, {
      officer_email: officerEmail,
      resolution_status: resolution,
      notes: notes || '',
    });
    return res.data;
  },
  verifyConnector: async (payload) => {
    const res = await apiClient.post('/verification/connector/verify', payload);
    return res.data;
  },
  compositeVerifyConnector: async (payload) => {
    const res = await apiClient.post('/verification/connector/composite-verify', payload);
    return res.data;
  },

  // Forensics Engine & Proof-of-Reality
  analyzeDocumentForensics: async (formData) => {
    const res = await apiClient.post('/forensics/document/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  checkSunShadowPlausibility: async (formData) => {
    const res = await apiClient.post('/forensics/photo/sun-shadow-plausibility', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  checkBuiltUpPlausibility: async (formData) => {
    const res = await apiClient.post('/forensics/geospatial/built-up-plausibility', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  getForensicsCalibration: async () => {
    const res = await apiClient.get('/forensics/calibration');
    return res.data;
  },
  runForensicsCalibration: async (params = {}) => {
    const res = await apiClient.post('/forensics/calibrate', null, { params });
    return res.data;
  },

  // Inspection Planner
  getInspectionPlanner: async (params = {}) => {
    const res = await apiClient.get('/inspections/planner', { params });
    return res.data;
  },

  // Pre-Flight Readiness
  runPreflight: async (instId, category, facts) => {
    const res = await apiClient.post('/preflight/scan', {
      institution_id: instId,
      application_category: category,
      facts: facts || {},
    });
    return res.data;
  },
  uploadPreflightDocument: async (instId, docType, file) => {
    const formData = new FormData();
    formData.append('institution_id', instId);
    if (docType) formData.append('document_type', docType);
    formData.append('file', file);
    const res = await apiClient.post('/preflight/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  ingestDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/documents/ingest', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  // National Photo Reuse Radar
  getRadarClusters: async () => {
    const res = await apiClient.get('/radar/clusters');
    return res.data;
  },
  queryRadarPhoto: async (formData) => {
    const res = await apiClient.post('/radar/query', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};


