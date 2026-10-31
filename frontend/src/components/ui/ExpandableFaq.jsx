import React, { useState } from 'react';
import { ChevronDown, HelpCircle, ShieldCheck } from 'lucide-react';
import LastUpdated from './LastUpdated';

const FAQ_ITEMS = [
  {
    id: 'faq-natural-justice',
    question: 'How does PRAMAAN-X comply with Natural Justice and prevent automated rejection challenges?',
    category: 'Administrative Law',
    answer: 'Under administrative law, automated decisions without human application of mind violate natural justice (State of Orissa v. Dr. Bina Pani Dei). PRAMAAN-X is architecturally designed so that automated rejections are impossible under regulatory policy and enforced via database constraints. The platform produces only "Indicator for review". Every adverse determination requires an authorized officer\'s explicit review and reasoned rationale, anchored with an immutable cryptographic receipt.'
  },
  {
    id: 'faq-evidence-act',
    question: 'How does the cryptographic audit ledger satisfy Section 65B of the Indian Evidence Act?',
    category: 'Legal Admissibility',
    answer: 'Section 65B requires proof of computer system integrity, uncorrupted electronic custody, and timestamped audit logs. Every officer determination embeds the SHA-256 hash of the input dossier, payload digest, UTC timestamp, officer identity, and the cryptographic signature of the preceding block (prev_receipt_hash). Altering any historical finding invalidates subsequent hash pointers and immediately flags a tamper warning.'
  },
  {
    id: 'faq-dpdp-compliance',
    question: 'How is compliance with the Digital Personal Data Protection (DPDP) Act 2023 maintained?',
    category: 'Data Privacy',
    answer: 'PRAMAAN-X implements strict Data Minimization under Section 6 of DPDP 2023. Plaintext Aadhaar and biometric numbers are never rendered or stored unmasked; all UI views and tables use masked strings (e.g. XXXX-XXXX-6057) and salted HMAC-SHA256 digests. Multi-institution faculty overlap checks evaluate cryptographic tokens without exposing underlying personal identifying information.'
  },
  {
    id: 'faq-scan-noise',
    question: 'How are poor scan quality, mobile photos, and blurred documents handled without false positives?',
    category: 'Forensics & Accuracy',
    answer: 'Forensic decision thresholds were calibrated against held-out benchmark sets containing blurred, skewed, and photocopied clean authentic scans. When a document is too degraded to extract or OCR confidently, the system never auto-rejects; instead, it automatically files a ticket in the Manual Review Queue with status "manual_review_required" for human verification.'
  },
  {
    id: 'faq-campus-sharing',
    question: 'What happens when sister institutions legitimately share a campus under the same Trust?',
    category: 'Knowledge Graph',
    answer: 'When Photo Radar detects visual similarity across facilities, it queries the Trust Knowledge Graph. If both institutions share the same registered Trust/Society ID, the finding is classified as "PERMITTED_CAMPUS_SHARING" rather than an adversarial duplicate, displaying an informational note rather than a statutory defect.'
  },
  {
    id: 'faq-scalability',
    question: 'Can the architecture scale to 10,000+ peak annual AICTE applications?',
    category: 'Scalability',
    answer: 'Yes. Benchmarked end-to-end dossier evaluation executes in ~2.08 seconds per application. Across 10,000 filings, compute workload is ~5.7 CPU hours, horizontally scalable across asynchronous Celery worker nodes. Vector similarity searches in FAISS execute in sub-12 milliseconds across 100,000 facility embeddings.'
  }
];

/**
 * ExpandableFaq - Accessible accordion component sourced strictly from official repo defense docs
 */
export default function ExpandableFaq({ className = '' }) {
  const [openIds, setOpenIds] = useState(new Set(['faq-natural-justice']));

  const toggleItem = (id) => {
    setOpenIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <section 
      id="system-architecture-faq"
      aria-label="System Architecture & Defense FAQ"
      className={`bg-surface rounded-2xl border border-border p-5 sm:p-6 shadow-card space-y-4 ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-border gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-primary/10 text-primary">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-text">
              Regulatory Architecture & Defense Q&A
            </h3>
            <p className="text-xs text-text-muted">
              Authoritative defenses regarding administrative law, DPDP 2023, and Section 65B compliance.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-3 h-3" />
            Statutory AICTE Defense
          </span>
        </div>
      </div>

      {/* Accordion List */}
      <div className="space-y-2">
        {FAQ_ITEMS.map((item) => {
          const isOpen = openIds.has(item.id);

          return (
            <div 
              key={item.id}
              className="border border-border rounded-xl overflow-hidden bg-surface-2/40 transition-colors"
            >
              <button
                type="button"
                id={`faq-btn-${item.id}`}
                aria-expanded={isOpen}
                aria-controls={`faq-content-${item.id}`}
                onClick={() => toggleItem(item.id)}
                className="w-full flex items-center justify-between p-3.5 sm:p-4 text-left transition-colors hover:bg-surface-2 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              >
                <div className="flex items-center gap-3 pr-2 min-w-0">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-surface border border-border text-text-muted shrink-0 hidden sm:inline-block">
                    {item.category}
                  </span>
                  <span className="text-xs font-semibold text-text">
                    {item.question}
                  </span>
                </div>
                <ChevronDown className={`w-4 h-4 text-text-muted shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180 text-primary' : ''}`} />
              </button>

              {isOpen && (
                <div 
                  id={`faq-content-${item.id}`}
                  role="region"
                  aria-labelledby={`faq-btn-${item.id}`}
                  className="px-4 pb-4 pt-1 text-xs text-text-muted leading-relaxed border-t border-border/50 bg-surface/50 animate-fadeIn"
                >
                  <p>{item.answer}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-text-muted border-t border-border gap-2">
        <span>Sourced from AICTE Evaluation & Regulatory Scrutiny Protocol</span>
        <LastUpdated />
      </div>
    </section>
  );
}

