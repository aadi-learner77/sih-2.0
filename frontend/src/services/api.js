import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

  // Audit Ledger
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

  // Pre-Flight Readiness
  runPreflight: async (instId, category, facts) => {
    const res = await apiClient.post('/preflight/scan', {
      institution_id: instId,
      application_category: category,
      facts: facts || {},
    });
    return res.data;
  },
};
