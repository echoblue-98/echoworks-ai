# Frontend → Backend Integration Guide

This guide shows how to connect your EchoWorks frontend (Canva or SvelteKit) to the Django backend.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      YOUR WEBSITE                            │
│  ┌─────────────────┐           ┌─────────────────────────┐  │
│  │  Canva Website  │──embed──▶ │  SvelteKit Frontend     │  │
│  │  (Marketing)    │           │  (Interactive Demos)    │  │
│  └─────────────────┘           └───────────┬─────────────┘  │
└────────────────────────────────────────────┼────────────────┘
                                             │
                                     HTTPS (JSON)
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    DJANGO BACKEND                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  /api/v1/                                            │   │
│  │    ├── catalog/products/                             │   │
│  │    ├── demos/document-analyze/    ◀──────────┐       │   │
│  │    ├── demos/threat-profile/      ◀──────────┤       │   │
│  │    ├── demos/agent-chat/          ◀──────────┤       │   │
│  │    ├── leads/roi-calculate/       ◀──────────┤       │   │
│  │    ├── bookings/demo-requests/    ◀──────────┤       │   │
│  │    └── payments/checkout/                    │       │   │
│  └──────────────────────────────────────────────┼───────┘   │
│                                                 │           │
│  ┌─────────────────────────────────────────────┴─────────┐  │
│  │  AION OS Modules (Real AI Processing)                 │  │
│  │    • document_intelligence.py                         │  │
│  │    • threat_profile.py                                │  │
│  │    • reasoning_engine.py                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Setting Up the Connection

### Step 1: Deploy Django Backend

**Option A: Railway (Recommended for quick start)**
```bash
cd c:\echoworks-backend
railway login
railway init
railway up
```
Your API will be at: `https://your-app.railway.app/api/v1/`

**Option B: Render**
```bash
# Just push to GitHub, Render auto-deploys from render.yaml
git push origin main
```

**Option C: Local Development**
```bash
cd c:\echoworks-backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
API available at: `http://localhost:8000/api/v1/`

### Step 2: Configure SvelteKit Frontend

Update the API base URL in `src/lib/api.ts`:

```typescript
// Development
const API_BASE = 'http://localhost:8000/api/v1';

// Production (replace with your deployed URL)
const API_BASE = 'https://your-app.railway.app/api/v1';
```

**Using environment variables (recommended):**

Create `.env`:
```
PUBLIC_API_BASE=https://your-backend.railway.app/api/v1
```

Update `src/lib/api.ts`:
```typescript
import { PUBLIC_API_BASE } from '$env/static/public';
const API_BASE = PUBLIC_API_BASE || 'http://localhost:8000/api/v1';
```

### Step 3: Deploy SvelteKit Frontend

**Vercel (Recommended):**
```bash
cd c:\codetyphoons-aionos26\aion-sveltekit
npm install -g vercel
vercel
```

**Cloudflare Pages:**
```bash
npm run build
# Upload _app to Cloudflare Pages
```

### Step 4: Connect Canva Website

**Option A: iFrame Embed (Simplest)**

In Canva, add an "Embed" element and paste:
```html
<iframe 
  src="https://your-svelte-app.vercel.app/demos" 
  width="100%" 
  height="800"
  frameborder="0"
></iframe>
```

**Option B: Link Buttons**

Add buttons in Canva linking to:
- `https://your-svelte-app.vercel.app/demos` → Try Live Demos
- `https://your-svelte-app.vercel.app/contact` → Book a Demo
- `https://your-svelte-app.vercel.app/pricing` → View Pricing

**Option C: Canva Connect (Advanced)**

Use Canva's App SDK for deeper integration:
```javascript
// In a Canva App
const result = await fetch('https://your-backend.railway.app/api/v1/demos/document-analyze/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ document_text: '...', document_type: 'contract' })
});
```

## API Endpoints Reference

### Demo Endpoints (No Auth Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/demos/document-analyze/` | POST | Analyze contracts/documents |
| `/demos/threat-profile/` | POST | Generate risk assessment |
| `/demos/agent-chat/` | POST | Chat with AI agent |
| `/leads/roi-calculate/` | POST | Calculate ROI savings |

### Catalog Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/catalog/products/` | GET | List all products |
| `/catalog/products/{id}/` | GET | Get product details |
| `/catalog/products/featured/` | GET | Featured products only |

### Example API Calls

**Document Analysis:**
```javascript
const response = await fetch('https://api.echoworks.ai/api/v1/demos/document-analyze/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    document_text: 'This Agreement grants exclusive rights in perpetuity...',
    document_type: 'contract'
  })
});
const analysis = await response.json();
// Returns: { risk_score, risk_level, clauses, red_flags, summary }
```

**Threat Profile:**
```javascript
const response = await fetch('https://api.echoworks.ai/api/v1/demos/threat-profile/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    risk_factors: ['contract_dispute', 'data_breach'],
    industry_context: 'technology',
    company_size: 'medium'
  })
});
const profile = await response.json();
// Returns: { composite_score, threats, recommendations, risk_dimensions }
```

**ROI Calculator:**
```javascript
const response = await fetch('https://api.echoworks.ai/api/v1/leads/roi-calculate/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    company_size: 50,
    avg_contract_value: 25000,
    contracts_per_month: 10,
    hours_per_contract: 4,
    hourly_rate: 150
  })
});
const roi = await response.json();
// Returns: { annual_savings, hours_saved, roi_percentage, payback_months }
```

## CORS Configuration

The Django backend is already configured to accept requests from any origin during development. For production, update `echoworks/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://your-svelte-app.vercel.app",
    "https://www.yourdomain.com",
]
```

## Testing the Integration

1. **Start Django backend:**
   ```bash
   cd c:\echoworks-backend
   python manage.py runserver
   ```

2. **Start SvelteKit frontend:**
   ```bash
   cd c:\codetyphoons-aionos26\aion-sveltekit
   npm run dev
   ```

3. **Open browser:**
   - Frontend: http://localhost:5173/demos
   - API Docs: http://localhost:8000/api/docs/

4. **Test each demo:**
   - Document Analyzer → Paste a contract → Click Analyze
   - Threat Profile → Select risk factors → Generate
   - ROI Calculator → Adjust sliders → Calculate
   - Agent Chat → Ask a question → Get response

## File Structure Summary

```
echoworks-backend/           # Django REST API
├── apps/
│   ├── demos/               # Live demo endpoints (calls AION OS)
│   ├── catalog/             # Products/pricing
│   ├── bookings/            # Demo scheduling
│   ├── leads/               # Lead capture + ROI calc
│   └── ...

aion-sveltekit/              # SvelteKit Frontend
├── src/
│   ├── lib/
│   │   ├── api.ts           # API client (calls Django)
│   │   └── components/
│   │       ├── DocumentAnalyzerDemo.svelte
│   │       ├── ThreatProfileDemo.svelte
│   │       ├── ROICalculatorDemo.svelte
│   │       └── AgentChatDemo.svelte
│   └── routes/
│       └── demos/+page.svelte

aionos/                      # AI Engine (imported by Django)
├── document_intelligence.py
├── threat_profile.py
└── reasoning_engine.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS errors | Check `CORS_ALLOWED_ORIGINS` in Django settings |
| 404 on API calls | Verify `API_BASE` URL includes `/api/v1` |
| Demos return sample data | Deploy AION OS modules with Django |
| Slow responses | Check if AION modules are loading properly |

---

**Your "True Developer" setup is complete!** Website visitors can now:
1. Browse products on your Canva marketing site
2. Click "Try Demo" → Opens SvelteKit interactive demos
3. Actually experience Document AI, Threat Profiling, etc.
4. Calculate their ROI savings
5. Book a demo through the booking system
6. Sign up and pay through the checkout flow
