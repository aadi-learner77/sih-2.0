const fs = require('fs');
const path = require('path');

function walk(dir) {
  let results = [];
  fs.readdirSync(dir).forEach(file => {
    file = path.join(dir, file);
    if (fs.statSync(file).isDirectory()) results = results.concat(walk(file));
    else if (file.endsWith('.jsx')) results.push(file);
  });
  return results;
}

walk('frontend/src').forEach(f => {
  const content = fs.readFileSync(f, 'utf8');
  const btnRegex = /<button[\s\S]*?<\/button>/g;
  let m;
  while ((m = btnRegex.exec(content)) !== null) {
    const text = m[0];
    if (text.includes('emerald') || text.includes('green')) {
      const cls = text.match(/className=(?:["'{`])([\s\S]*?)(?:["'}`])/);
      console.log(f + ' -> ' + (cls ? cls[1].replace(/\s+/g, ' ').slice(0, 100) : 'no class'));
    }
  }
});

