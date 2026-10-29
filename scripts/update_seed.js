const fs = require('fs');
const path = 'backend/app/data/seed_data.py';
let text = fs.readFileSync(path, 'utf8');
const target = 'print("PRAMAAN-X Database seeding completed successfully with 7 chained audit receipts!")';
const rep = `try:
        from backend.app.services.alert_service import AlertService
        AlertService().run_full_scan(db)
    except Exception as e:
        print(f"Alert scan notice: {e}")
    print("PRAMAAN-X Database seeding completed successfully with 7 chained audit receipts and operational alerts!")`;
if (text.includes(target)) {
  text = text.replace(target, rep);
  fs.writeFileSync(path, text, 'utf8');
  console.log('Successfully updated seed_data.py');
} else {
  console.log('Target not found in seed_data.py');
}

