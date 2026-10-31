with open('frontend/src/pages/DocumentIntelligencePage.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

target1 = '''                  className={`h-8 px-3 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-primary/10 border-primary text-primary font-semibold'
                      : 'bg-surface border-border text-muted hover:text-text hover:bg-surface-2'
                  }`}'''

repl1 = '''                  className={`h-8 px-3 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                    isSelected
                      ? 'btn-solid shadow-xs'
                      : 'bg-surface border-border text-text-muted hover:text-text hover:bg-surface-2'
                  }`}'''

target2 = '''                    className={`h-8 px-2.5 rounded-lg text-xs font-medium border flex items-center space-x-1 transition-colors cursor-pointer ${
                      showBoxes
                        ? 'bg-primary/10 border-primary text-primary'
                        : 'bg-surface border-border text-muted hover:text-text'
                    }`}'''

repl2 = '''                    className={`h-8 px-2.5 rounded-lg text-xs font-medium border flex items-center space-x-1 transition-colors cursor-pointer ${
                      showBoxes
                        ? 'btn-solid shadow-xs'
                        : 'bg-surface border-border text-text-muted hover:text-text'
                    }`}'''

assert target1 in c, 'target1 not found'
assert target2 in c, 'target2 not found'

c = c.replace(target1, repl1).replace(target2, repl2)
with open('frontend/src/pages/DocumentIntelligencePage.jsx', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

print('Updated sample doc & toggle boxes to btn-solid')

