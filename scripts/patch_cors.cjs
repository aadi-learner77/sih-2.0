const fs = require('fs');
let main = fs.readFileSync('backend/app/main.py', 'utf8');

const target = `# CORS Middleware
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if not cors_origins or "*" in cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)`;

const replacement = `# CORS Middleware
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip() and o.strip() != "*"]
if not cors_origins:
    cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)`;

main = main.replace(target, replacement).replace(target.replace(/\n/g, '\r\n'), replacement.replace(/\n/g, '\r\n'));
fs.writeFileSync('backend/app/main.py', main, 'utf8');
console.log('Successfully updated CORS configuration in backend/app/main.py');

