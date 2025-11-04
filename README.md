
---

### **2️⃣ Visual Testing & Link Verification**

After you’ve saved your routes:
- Load the Excel file  
- Visit each route one by one  
- Capture screenshots or verify HTTP responses  
- Compare against a previous version for visual/UI differences

---

## 🧠 Features

| Function | Description |
|-----------|--------------|
| **Visual Regression Testing** | Compares screenshots between old and new deployments. Flags pixel differences beyond a threshold. |
| **Link Verification** | Checks each saved route for status codes (`200`, `301`, `404`, etc.) and logs broken links. |
| **Excel Integration** | Reads routes directly from generated Excel reports. |
| **Automatic Reports** | Saves comparison results and screenshots under `reports/visual_tests/` and `reports/link_reports/`. |

---

## 🪜 Setup

### 1️⃣ Install Dependencies
```bash
pip install playwright pandas openpyxl pillow
playwright install chromium
