const fs = require('fs');
let nav = fs.readFileSync('frontend/src/components/Navbar.jsx', 'utf8');

// Add id="header-signout-btn"
nav = nav.replace(
  '{onLogout && (\n              <button\n                onClick={onLogout}',
  '{onLogout && (\n              <button\n                id="header-signout-btn"\n                onClick={onLogout}'
).replace(
  '{onLogout && (\r\n              <button\r\n                onClick={onLogout}',
  '{onLogout && (\r\n              <button\r\n                id="header-signout-btn"\r\n                onClick={onLogout}'
);

// Add id="header-role-select"
nav = nav.replace(
  '<UserCheck className="w-4 h-4 ml-2 text-sky-600 shrink-0" />\n              <select\n                value={currentRole}',
  '<UserCheck className="w-4 h-4 ml-2 text-sky-600 shrink-0" />\n              <select\n                id="header-role-select"\n                value={currentRole}'
).replace(
  '<UserCheck className="w-4 h-4 ml-2 text-sky-600 shrink-0" />\r\n              <select\r\n                value={currentRole}',
  '<UserCheck className="w-4 h-4 ml-2 text-sky-600 shrink-0" />\r\n              <select\r\n                id="header-role-select"\r\n                value={currentRole}'
);

fs.writeFileSync('frontend/src/components/Navbar.jsx', nav, 'utf8');
console.log('Updated Navbar.jsx');

