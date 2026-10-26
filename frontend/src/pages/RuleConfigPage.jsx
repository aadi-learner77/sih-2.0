import React, { useState, useEffect } from 'react';
import { 
  BookOpenCheck, 
  Settings2, 
  CheckCircle2, 
  Save, 
  RotateCw, 
  Scale, 
  Code2, 
  FileCode,
  Sliders
} from 'lucide-react';
import { api } from '../services/api';

export default function RuleConfigPage() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingRule, setEditingRule] = useState(null);
  const [editParams, setEditParams] = useState({});
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const fetchRules = async () => {
    setLoading(true);
    try {
      const data = await api.getRules();
      setRules(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleEditClick = (rule) => {
    setEditingRule(rule);
    setEditParams(rule.parameters ? { ...rule.parameters } : {});
    setSuccessMsg('');
  };

  const handleSaveRule = async () => {
    if (!editingRule) return;
    setSaving(true);
    try {
      await api.updateRule(editingRule.id, {
        parameters: editParams
      });
      setSuccessMsg(`Rule ${editingRule.clause_id} parameters updated and hot-reloaded in YAML engine!`);
      fetchRules();
      setEditingRule(null);
    } catch (err) {
      console.error(err);
      alert('Failed to update rule');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-purple-50 via-white to-slate-50 border border-purple-200/70 rounded-2xl p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-purple-700 uppercase tracking-widest mb-1">
              <span>Regulation-as-Code Engine</span>
              <span>•</span>
              <span>Configurable YAML Architecture</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              AICTE Handbook Clauses & Dynamic Rule Sets
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Clauses from the AICTE Approval Process Handbook (APH 2025-26) are codified as declarative, auditable YAML rule definitions. Zero hard-coded logic: regulatory thresholds can be revised dynamically.
            </p>
          </div>

          <button
            onClick={fetchRules}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-xs shrink-0"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Reload Rules from Disk</span>
          </button>
        </div>

        {successMsg && (
          <div className="mt-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rules.map((rule) => {
          const isSelected = editingRule?.id === rule.id;
          return (
            <div 
              key={rule.id}
              className={`bg-white border rounded-2xl p-5 transition-all flex flex-col justify-between shadow-xs ${
                isSelected ? 'border-purple-300 shadow-md ring-1 ring-purple-200' : 'border-slate-200 hover:border-purple-200 hover:shadow-sm'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="space-y-0.5">
                    <span className="text-xs font-mono font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                      {rule.clause_id}
                    </span>
                    <h2 className="text-sm font-bold text-slate-900 mt-1.5 leading-snug">{rule.clause_title}</h2>
                  </div>
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border shrink-0 ${
                    rule.severity === 'CRITICAL' ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}>
                    {rule.severity}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed mb-4">
                  {rule.description}
                </p>

                {/* Condition Code Expression */}
                <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 mb-4 font-mono text-[11px] text-slate-600 space-y-1">
                  <div className="flex items-center space-x-1.5 text-slate-500 text-[10px] uppercase font-semibold">
                    <Code2 className="w-3 h-3 text-sky-600" />
                    <span>Evaluated Condition</span>
                  </div>
                  <div className="text-sky-800 font-semibold truncate">{rule.condition}</div>
                </div>

                {/* Parameters Display */}
                <div className="space-y-1.5 mb-4">
                  <div className="text-[11px] text-slate-500 uppercase font-semibold">Active Parameters:</div>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(rule.parameters || {}).map(([key, val]) => (
                      <span key={key} className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-slate-800 font-mono">
                        {key}: <strong className="text-purple-700">{String(val)}</strong>
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Edit Controls */}
              <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-mono">
                  {rule.handbook_edition}
                </span>
                <button
                  onClick={() => handleEditClick(rule)}
                  className="flex items-center space-x-1.5 text-xs text-purple-700 hover:text-purple-800 font-semibold px-3 py-1.5 rounded-lg bg-purple-50 border border-purple-200 hover:bg-purple-100 transition-colors"
                >
                  <Sliders className="w-3.5 h-3.5" />
                  <span>Configure Clause</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* In-Line Rule Configuration Modal */}
      {editingRule && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-purple-200 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-mono font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                  {editingRule.clause_id}
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-1">Configure Regulatory Parameters</h3>
              </div>
              <button 
                onClick={() => setEditingRule(null)}
                className="text-slate-400 hover:text-slate-700 text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Modifications are written directly to <code className="text-purple-700 font-semibold">aicte_aph_2025.yaml</code> and reloaded by the runtime rule engine without server downtime.
            </p>

            <div className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
              {Object.keys(editParams).length === 0 ? (
                <div className="text-xs text-slate-500">This clause has no configurable numeric parameters.</div>
              ) : (
                Object.entries(editParams).map(([key, val]) => (
                  <div key={key} className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 font-mono">{key}</label>
                    <input
                      type="text"
                      value={val}
                      onChange={(e) => {
                        const newParams = { ...editParams };
                        const inputVal = e.target.value;
                        newParams[key] = isNaN(Number(inputVal)) ? inputVal : Number(inputVal);
                        setEditParams(newParams);
                      }}
                      className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-900 focus:outline-none focus:border-purple-500 transition-colors"
                    />
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => setEditingRule(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200 border border-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveRule}
                disabled={saving}
                className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-sm flex items-center space-x-2"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? 'Updating YAML...' : 'Save & Hot-Reload'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
