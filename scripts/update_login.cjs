const fs = require('fs');
let login = fs.readFileSync('frontend/src/pages/LoginPage.jsx', 'utf8');

// Add id="login-submit-btn"
login = login.replace(
  '<button\n              type="submit"',
  '<button\n              id="login-submit-btn"\n              type="submit"'
).replace(
  '<button\r\n              type="submit"',
  '<button\r\n              id="login-submit-btn"\r\n              type="submit"'
);

// Add id={`preset-role-${preset.role}`}
login = login.replace(
  '<button\n                    key={preset.role}\n                    type="button"\n                    onClick={() => handleSelectPreset(preset)}',
  '<button\n                    key={preset.role}\n                    id={`preset-role-${preset.role}`}\n                    type="button"\n                    onClick={() => handleSelectPreset(preset)}'
).replace(
  '<button\r\n                    key={preset.role}\r\n                    type="button"\r\n                    onClick={() => handleSelectPreset(preset)}',
  '<button\r\n                    key={preset.role}\r\n                    id={`preset-role-${preset.role}`}\r\n                    type="button"\r\n                    onClick={() => handleSelectPreset(preset)}'
);

fs.writeFileSync('frontend/src/pages/LoginPage.jsx', login, 'utf8');
console.log('Updated LoginPage.jsx');

