with open('frontend/src/components/EvidenceLens.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

target1 = '''                  className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all cursor-pointer flex items-center space-x-1.5 ${
                    isSelected
                      ? 'bg-primary text-white border-primary shadow-xs'
                      : 'bg-surface-2 border-border text-text-muted hover:text-text hover:bg-surface'
                  }`}'''
repl1 = '''                  className={`tab px-3 py-1 rounded-full text-xs font-semibold border transition-all cursor-pointer flex items-center space-x-1.5 ${
                    isSelected
                      ? 'is-active btn-solid shadow-xs'
                      : 'btn-outline'
                  }`}'''

target2 = '''                id="btn-submit-officer-action"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"'''
repl2 = '''                id="btn-submit-officer-action"
                disabled={isSubmitting}
                className="btn-solid w-full py-2.5 px-4 rounded-xl bg-primary hover:bg-primary-hover text-on-primary text-xs font-bold transition-all shadow-xs flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"'''

assert target1 in c, 'target1 not found'
assert target2 in c, 'target2 not found'

c = c.replace(target1, repl1).replace(target2, repl2)
with open('frontend/src/components/EvidenceLens.jsx', 'w', encoding='utf-8', newline='') as f:
    f.write(c)
print('EvidenceLens updated successfully')

