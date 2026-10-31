import os

def update_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    initial = content
    for target, repl in replacements:
        if target not in content:
            print(f"FAILED to find target in {path}: {target[:40]}...")
            return False
        content = content.replace(target, repl)
        
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print(f"Successfully updated {path}")
    return True

# 1. RuleConfigPage.jsx
rc_repls = [
    (
        '''        <button
          id="tab-rules-catalog"
          onClick={() => setActiveTopTab('catalog')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 cursor-pointer ${
            activeTopTab === 'catalog'
              ? 'bg-purple-700 text-white shadow-sm'
              : 'text-text-muted hover:text-text hover:bg-surface-2'
          }`}
        >''',
        '''        <button
          id="tab-rules-catalog"
          role="tab"
          aria-selected={activeTopTab === 'catalog'}
          onClick={() => setActiveTopTab('catalog')}
          className={`tab px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 cursor-pointer ${
            activeTopTab === 'catalog'
              ? 'is-active btn-solid shadow-sm'
              : 'text-text-muted hover:text-text hover:bg-surface-2'
          }`}
        >'''
    ),
    (
        '''        <button
          id="tab-what-if-simulator"
          onClick={() => setActiveTopTab('simulator')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 cursor-pointer ${
            activeTopTab === 'simulator'
              ? 'bg-purple-700 text-white shadow-sm'
              : 'text-text-muted hover:text-text hover:bg-surface-2'
          }`}
        >''',
        '''        <button
          id="tab-what-if-simulator"
          role="tab"
          aria-selected={activeTopTab === 'simulator'}
          onClick={() => setActiveTopTab('simulator')}
          className={`tab px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 cursor-pointer ${
            activeTopTab === 'simulator'
              ? 'is-active btn-solid shadow-sm'
              : 'text-text-muted hover:text-text hover:bg-surface-2'
          }`}
        >'''
    ),
    (
        'className="py-2.5 px-5 rounded-xl bg-gradient-to-r from-purple-700 to-indigo-700 hover:from-purple-800 hover:to-indigo-800 text-white text-xs font-bold shadow-md shadow-purple-500/20 transition-all flex items-center space-x-2 active:scale-95 cursor-pointer"',
        'className="btn-solid py-2.5 px-5 rounded-xl bg-gradient-to-r from-purple-700 to-indigo-700 hover:from-purple-800 hover:to-indigo-800 text-white text-xs font-bold shadow-md shadow-purple-500/20 transition-all flex items-center space-x-2 active:scale-95 cursor-pointer"'
    ),
    (
        'className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-xs flex items-center space-x-2 active:scale-95 cursor-pointer"',
        'className="btn-solid px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-xs flex items-center space-x-2 active:scale-95 cursor-pointer"'
    )
]
update_file('frontend/src/pages/RuleConfigPage.jsx', rc_repls)

# 2. RulesCatalogView.jsx
cat_repls = [
    (
        '''          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-purple-600 text-white shadow-2xs'
                  : 'bg-surface border border-border text-text-muted hover:bg-surface-2'
              }`}
            >
              {cat === 'ALL' ? 'All Regulations' : cat}
            </button>
          ))}''',
        '''          {categories.map((cat) => (
            <button
              key={cat}
              role="tab"
              aria-selected={selectedCategory === cat}
              onClick={() => setSelectedCategory(cat)}
              className={`tab px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                selectedCategory === cat
                  ? 'is-active btn-solid shadow-2xs'
                  : 'btn-outline'
              }`}
            >
              {cat === 'ALL' ? 'All Regulations' : cat}
            </button>
          ))}'''
    )
]
update_file('frontend/src/components/RulesCatalogView.jsx', cat_repls)

# 3. ManualReviewQueuePage.jsx
mrq_repls = [
    (
        '''                    <button
                      id={`verify-now-${item.queue_id}`}
                      onClick={() => handleVerifyNow(item)}
                      disabled={isVerifying}
                      className="h-9 px-4 rounded-xl text-xs font-semibold bg-surface-2/80 hover:bg-surface text-text border border-border backdrop-blur-md transition-all shadow-xs flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
                    >''',
        '''                    <button
                      id={`verify-now-${item.queue_id}`}
                      onClick={() => handleVerifyNow(item)}
                      disabled={isVerifying}
                      className="btn-outline h-9 px-4 rounded-xl text-xs font-semibold hover:bg-surface text-text border border-border transition-all shadow-xs flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
                    >'''
    ),
    (
        '''                    <button
                      id={`resolve-btn-${item.queue_id}`}
                      onClick={() => {
                        setResolveItem(item);
                        setResolveStatus(item.status === 'RESOLVED' ? 'RESOLVED' : 'VERIFIED');
                      }}
                      className="h-9 px-4 bg-primary hover:bg-primary-hover text-white rounded-xl text-xs font-semibold transition-all shadow-md shadow-primary/25 flex items-center space-x-1.5 cursor-pointer"
                    >
                      Resolve Ticket
                    </button>''',
        '''                    <button
                      id={`resolve-btn-${item.queue_id}`}
                      onClick={() => {
                        setResolveItem(item);
                        setResolveStatus(item.status === 'RESOLVED' ? 'RESOLVED' : 'VERIFIED');
                      }}
                      className="btn-solid h-9 px-4 rounded-xl text-xs font-semibold transition-all shadow-md flex items-center space-x-1.5 cursor-pointer"
                    >
                      Resolve Ticket
                    </button>'''
    ),
    (
        '''              <button
                type="button"
                id="btn-confirm-resolve-ticket"
                disabled={resolving || !resolveNotes.trim()}
                onClick={handleResolveSubmit}
                className="h-10 px-5 text-xs font-semibold rounded-xl shadow-xs transition-colors cursor-pointer flex items-center space-x-1.5 bg-primary hover:bg-primary-hover text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >''',
        '''              <button
                type="button"
                id="btn-confirm-resolve-ticket"
                disabled={resolving || !resolveNotes.trim()}
                onClick={handleResolveSubmit}
                className="btn-solid h-10 px-5 text-xs font-semibold rounded-xl shadow-xs transition-colors cursor-pointer flex items-center space-x-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >'''
    ),
    (
        '''              <button
                type="button"
                onClick={() => setResolveItem(null)}
                className="h-10 px-4 text-xs font-semibold text-text-muted hover:text-text rounded-lg hover:bg-surface-2 transition-colors cursor-pointer"
              >
                Cancel
              </button>''',
        '''              <button
                type="button"
                onClick={() => setResolveItem(null)}
                className="btn-ghost h-10 px-4 text-xs font-semibold text-text-muted hover:text-text rounded-lg hover:bg-surface-2 transition-colors cursor-pointer"
              >
                Cancel
              </button>'''
    )
]
update_file('frontend/src/pages/ManualReviewQueuePage.jsx', mrq_repls)

# 4. DocumentIntelligencePage.jsx
doc_repls = [
    (
        '''                    <button
                      type="button"
                      onClick={() => setActiveViewMode('visual')}
                      className={`pb-1 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                        activeViewMode === 'visual'
                          ? 'border-primary text-primary'
                          : 'border-transparent text-muted hover:text-text'
                      }`}
                    >
                      Preview
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveViewMode('text')}
                      className={`pb-1 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                        activeViewMode === 'text'
                          ? 'border-primary text-primary'
                          : 'border-transparent text-muted hover:text-text'
                      }`}
                    >
                      Extracted text
                    </button>''',
        '''                    <button
                      type="button"
                      role="tab"
                      aria-selected={activeViewMode === 'visual'}
                      onClick={() => setActiveViewMode('visual')}
                      className={`tab px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                        activeViewMode === 'visual'
                          ? 'is-active btn-solid'
                          : 'text-text-muted hover:text-text hover:bg-surface-2'
                      }`}
                    >
                      Preview
                    </button>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={activeViewMode === 'text'}
                      onClick={() => setActiveViewMode('text')}
                      className={`tab px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                        activeViewMode === 'text'
                          ? 'is-active btn-solid'
                          : 'text-text-muted hover:text-text hover:bg-surface-2'
                      }`}
                    >
                      Extracted text
                    </button>'''
    ),
    (
        '''                className="h-8 px-3 rounded-lg bg-primary hover:bg-primary/90 text-white font-semibold text-xs flex items-center space-x-1.5 transition-colors cursor-pointer shadow-xs"''',
        '''                className="btn-solid h-8 px-3 rounded-lg bg-primary hover:bg-primary-hover text-on-primary font-semibold text-xs flex items-center space-x-1.5 transition-colors cursor-pointer shadow-xs"'''
    )
]
update_file('frontend/src/pages/DocumentIntelligencePage.jsx', doc_repls)

# 5. AuditAndReceiptsPage.jsx
audit_repls = [
    (
        '''          <button
            id="tab-receipts-timeline"
            onClick={() => setViewMode('timeline')}
            className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
              viewMode === 'timeline'
                ? 'bg-primary text-white shadow-sm'
                : 'text-text-muted hover:text-text hover:bg-surface-2'
            }`}
          >''',
        '''          <button
            id="tab-receipts-timeline"
            role="tab"
            aria-selected={viewMode === 'timeline'}
            onClick={() => setViewMode('timeline')}
            className={`tab px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
              viewMode === 'timeline'
                ? 'is-active btn-solid shadow-sm'
                : 'text-text-muted hover:text-text hover:bg-surface-2'
            }`}
          >'''
    ),
    (
        '''          <button
            id="tab-verification-statuses"
            onClick={() => setViewMode('table')}
            className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
              viewMode === 'table'
                ? 'bg-primary text-white shadow-sm'
                : 'text-text-muted hover:text-text hover:bg-surface-2'
            }`}
          >''',
        '''          <button
            id="tab-verification-statuses"
            role="tab"
            aria-selected={viewMode === 'table'}
            onClick={() => setViewMode('table')}
            className={`tab px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
              viewMode === 'table'
                ? 'is-active btn-solid shadow-sm'
                : 'text-text-muted hover:text-text hover:bg-surface-2'
            }`}
          >'''
    ),
    (
        '''          <button
            id="tab-officer-decisions"
            onClick={() => setViewMode('officer-decisions')}
            className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
              viewMode === 'officer-decisions'
                ? 'bg-primary text-white shadow-sm'
                : 'text-text-muted hover:text-text hover:bg-surface-2'
            }`}
          >''',
        '''          <button
            id="tab-officer-decisions"
            role="tab"
            aria-selected={viewMode === 'officer-decisions'}
            onClick={() => setViewMode('officer-decisions')}
            className={`tab px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
              viewMode === 'officer-decisions'
                ? 'is-active btn-solid shadow-sm'
                : 'text-text-muted hover:text-text hover:bg-surface-2'
            }`}
          >'''
    ),
    (
        '''          <button
            id="tab-manual-review-queue"
            onClick={() => setViewMode('manual-review-queue')}
            className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
              viewMode === 'manual-review-queue'
                ? 'bg-primary text-white shadow-sm'
                : 'text-text-muted hover:text-text hover:bg-surface-2'
            }`}
          >''',
        '''          <button
            id="tab-manual-review-queue"
            role="tab"
            aria-selected={viewMode === 'manual-review-queue'}
            onClick={() => setViewMode('manual-review-queue')}
            className={`tab px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
              viewMode === 'manual-review-queue'
                ? 'is-active btn-solid shadow-sm'
                : 'text-text-muted hover:text-text hover:bg-surface-2'
            }`}
          >'''
    ),
    (
        '''          <button
            id="tab-access-logs"
            onClick={() => setViewMode('access-logs')}
            className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
              viewMode === 'access-logs'
                ? 'bg-primary text-white shadow-sm'
                : 'text-text-muted hover:text-text hover:bg-surface-2'
            }`}
          >''',
        '''          <button
            id="tab-access-logs"
            role="tab"
            aria-selected={viewMode === 'access-logs'}
            onClick={() => setViewMode('access-logs')}
            className={`tab px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
              viewMode === 'access-logs'
                ? 'is-active btn-solid shadow-sm'
                : 'text-text-muted hover:text-text hover:bg-surface-2'
            }`}
          >'''
    )
]
update_file('frontend/src/pages/AuditAndReceiptsPage.jsx', audit_repls)

# 6. EvidenceLens.jsx
el_repls = [
    (
        '''                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center space-x-1.5 cursor-pointer ${
                    isSelected
                      ? 'bg-primary text-white border-primary shadow-xs'
                      : 'bg-surface-2 border-border text-text-muted hover:text-text hover:bg-surface'
                  }`}''',
        '''                  className={`tab px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center space-x-1.5 cursor-pointer ${
                    isSelected
                      ? 'is-active btn-solid shadow-xs'
                      : 'btn-outline'
                  }`}'''
    ),
    (
        '''                id="btn-submit-officer-action"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"''',
        '''                id="btn-submit-officer-action"
                disabled={isSubmitting}
                className="btn-solid w-full py-2.5 px-4 rounded-xl bg-primary hover:bg-primary-hover text-on-primary text-xs font-bold transition-all shadow-xs flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"'''
    )
]
update_file('frontend/src/components/EvidenceLens.jsx', el_repls)

# 7. Dashboard.jsx
dash_repls = [
    (
        '''                  id="launch-preflight-btn"
                  onClick={() => onNavigateTab('preflight')}
                  className="h-10 px-4 rounded-lg bg-[#0B3D91] hover:bg-[#0B3D91]/90 text-white dark:bg-[#3B6CFF] dark:hover:bg-[#3B6CFF]/90 dark:text-white text-xs font-semibold transition-colors flex items-center space-x-2 cursor-pointer shadow-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"''',
        '''                  id="launch-preflight-btn"
                  onClick={() => onNavigateTab('preflight')}
                  className="btn-solid h-10 px-4 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-2 cursor-pointer shadow-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"'''
    ),
    (
        '''                  id="launch-evidence-lens-btn"
                  onClick={() => onNavigateTab('evidence-lens')}
                  className="h-10 px-4 rounded-lg bg-[#0B3D91] hover:bg-[#0B3D91]/90 text-white dark:bg-[#3B6CFF] dark:hover:bg-[#3B6CFF]/90 dark:text-white text-xs font-semibold transition-colors flex items-center space-x-2 cursor-pointer shadow-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"''',
        '''                  id="launch-evidence-lens-btn"
                  onClick={() => onNavigateTab('evidence-lens')}
                  className="btn-solid h-10 px-4 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-2 cursor-pointer shadow-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"'''
    ),
    (
        '''                id="launch-audit-ledger-btn"
                onClick={() => onNavigateTab('audit-ledger')}
                className="h-10 px-4 rounded-lg border border-border text-text hover:bg-surface-2 text-xs font-semibold transition-colors flex items-center space-x-2 cursor-pointer shadow-2xs focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"''',
        '''                id="launch-audit-ledger-btn"
                onClick={() => onNavigateTab('audit-ledger')}
                className="btn-outline h-10 px-4 rounded-lg border border-border text-text hover:bg-surface-2 text-xs font-semibold transition-colors flex items-center space-x-2 cursor-pointer shadow-2xs focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"'''
    )
]
update_file('frontend/src/pages/Dashboard.jsx', dash_repls)
print("ALL POLISH REPLACEMENTS COMPLETED.")

