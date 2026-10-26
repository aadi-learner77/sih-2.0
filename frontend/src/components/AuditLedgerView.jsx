import React, { useState, useEffect } from 'react';
import { 
  FileCheck2, 
  ShieldCheck, 
  ShieldAlert, 
  Link2, 
  RefreshCw, 
  AlertOctagon, 
  KeyRound, 
  Clock, 
  Lock,
  CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';

export default function AuditLedgerView() {
  const [receipts, setReceipts] = useState([]);
  const [verificationResult, setVerificationResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [tampering, setTampering] = useState(false);
  const [tamperNotice, setTamperNotice] = useState(null);

  const fetchReceipts = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditReceipts();
      setReceipts(data);
      // Auto-verify on fetch
      const vResult = await api.verifyAuditChain();
      setVerificationResult(vResult);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReceipts();
  }, []);

  const handleManualVerify = async () => {
    setVerifying(true);
    try {
      const vResult = await api.verifyAuditChain();
      setVerificationResult(vResult);
    } catch (err) {
      console.error(err);
    } finally {
      setVerifying(false);
    }
  };

  const handleSimulateTamper = async () => {
    if (!confirm('This will subtly modify block #2 in the database to demonstrate automated cryptographic breach detection. Proceed?')) {
      return;
    }
    setTampering(true);
    try {
      const tRes = await api.simulateTampering(2);
      setTamperNotice(tRes);
      // Immediately run verification to show tamper detection
      const vResult = await api.verifyAuditChain();
      setVerificationResult(vResult);
    } catch (err) {
      console.error(err);
    } finally {
      setTampering(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-emerald-50 via-white to-slate-50 border border-emerald-200/70 rounded-2xl p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-800 uppercase tracking-widest mb-1">
              <span>Cryptographic Chain of Custody</span>
              <span>•</span>
              <span>Audit Compliance</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Tamper-Evident Verification Receipts Ledger
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Every application action, OCR scan, external registry lookup, and officer determination generates an immutable, cryptographically chained SHA-256 block receipt.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={handleManualVerify}
              disabled={verifying}
              className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>{verifying ? 'Verifying Chain...' : 'Verify Cryptographic Integrity'}</span>
            </button>

            <button
              onClick={handleSimulateTamper}
              disabled={tampering}
              className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-semibold transition-all shadow-xs"
            >
              <AlertOctagon className="w-4 h-4 text-rose-600" />
              <span>{tampering ? 'Simulating...' : 'Simulate Tampering Demo'}</span>
            </button>
          </div>
        </div>

        {/* Live Integrity Status Card */}
        {verificationResult && (
          <div className="mt-6 pt-6 border-t border-slate-200/80">
            {verificationResult.is_intact ? (
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center justify-between shadow-xs">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-emerald-900">
                      Ledger Integrity Authenticated: 100% Tamper-Free
                    </div>
                    <div className="text-xs text-emerald-700 font-mono">
                      All {verificationResult.chain_length} SHA-256 chained blocks mathematically validated from Genesis block.
                    </div>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold px-3 py-1 bg-white text-emerald-800 rounded-full border border-emerald-200 shadow-xs">
                  CHAIN INTACT
                </span>
              </div>
            ) : (
              <div className="bg-rose-50 border-2 border-rose-400 rounded-xl p-4 space-y-2 animate-pulse shadow-xs">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center shrink-0">
                    <ShieldAlert className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-rose-900">
                      CRYPTOGRAPHIC TAMPERING DETECTED!
                    </div>
                    <div className="text-xs text-rose-700 font-mono">
                      {verificationResult.tampered_receipts_count} receipt block(s) failed parent hash or digital signature verification.
                    </div>
                  </div>
                </div>
                {verificationResult.tamper_diagnostics && verificationResult.tamper_diagnostics.length > 0 && (
                  <div className="text-xs text-rose-800 pl-12 font-mono">
                    Breach point: Receipt #{verificationResult.tamper_diagnostics[0].receipt_index} ({verificationResult.tamper_diagnostics[0].details})
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Blockchain Receipts Flow */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
            <Link2 className="w-4 h-4 text-emerald-600" />
            <span>Chained Verification Receipts ({receipts.length} Blocks)</span>
          </h2>
          <span className="text-xs text-slate-500 font-mono font-medium">HMAC-SHA256 Signed</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500 text-xs">Loading audit blocks...</div>
        ) : (
          <div className="space-y-3">
            {receipts.map((receipt) => {
              const isGenesis = receipt.receipt_index === 0;
              return (
                <div 
                  key={receipt.id}
                  className="bg-white border border-slate-200 rounded-xl p-4 hover:border-slate-300 shadow-xs transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                    <div className="flex items-center space-x-3">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                        Block #{receipt.receipt_index} {isGenesis && '(Genesis)'}
                      </span>
                      <span className="text-xs font-bold text-slate-900">{receipt.event_type}</span>
                    </div>
                    <div className="flex items-center space-x-3 text-xs text-slate-500">
                      <div className="flex items-center space-x-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{new Date(receipt.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-[10px] text-slate-700 font-medium">
                        {receipt.actor_role} ({receipt.actor_email})
                      </span>
                    </div>
                  </div>

                  {/* Hash Chain Details */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] font-mono bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <div className="truncate">
                      <span className="text-slate-500">Previous Hash: </span>
                      <span className="text-slate-700">{receipt.previous_hash}</span>
                    </div>
                    <div className="truncate">
                      <span className="text-slate-500">Payload SHA-256: </span>
                      <span className="text-emerald-700">{receipt.payload_hash}</span>
                    </div>
                    <div className="truncate md:col-span-2">
                      <span className="text-slate-500">Receipt Block Hash: </span>
                      <span className="text-sky-700 font-bold">{receipt.receipt_hash}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
