# Devlancer AI – Multi-Tenant White-Label AI Chatbot SaaS Platform

A production-grade, multi-tenant, white-label AI Chatbot SaaS Platform engineered for **Devlancer** (`https://devstudios.in`) to deploy once and sell to multiple independent travel agencies and holiday companies under your own brand.

---

## 🌟 Key Platform Capabilities

1. **Multi-Tenant Data Isolation & Security**:
   - Single central FastAPI backend serving multiple independent client businesses simultaneously.
   - Built on an embedded SQLite database with **WAL (Write-Ahead Logging)** mode for high-concurrency read/writes without heavy external database dependencies (e.g. Postgres or Docker).
   - Strict tenant data scoping: each agency has isolated branding, holiday packages, conversation history, and captured leads.
   - Tenant-level website domain allowlisting (`allowed_domains`) preventing unauthorized widget embedding.
   - GDPR/Privacy compliance: Endpoints for session memory deletion and lead deletion.

2. **Universal Embeddable JavaScript Widget (`/widget.js`)**:
   - 1-line installation snippet that works on any website (WordPress, Shopify, Webflow, React, Next.js, static HTML):
     ```html
     <script src="http://localhost:8000/widget.js" data-assistant-id="asst_prakruthi_kammanahalli" defer></script>
     ```
   - **Shadow DOM Isolation**: The widget is mounted inside an isolated Shadow DOM tree (`#devlancer-ai-widget-root`), ensuring host website CSS and scripts never interfere with the chatbot.
   - **Maximize / Full-Screen view**: Smooth transition between floating widget and spacious full-screen mode.
   - **Interactive Travel Features**:
     - 🏷️ **View Packages**: Browses curated agency tour packages with durations and starting prices in INR.
     - 🧮 **Trip Cost Calculator**: Calculates estimated group budget (Adults + Seniors breakdown) and submits inquiries with 1 click.
     - 🎤 **Voice Input (STT)** & 🔊 **Speech Readout (TTS)** for accessible audio experience.
     - 📊 **Safe GFM Markdown Tables**: Clean comparison tables for itineraries and pricing.
     - 👍 / 👎 **Feedback Buttons**: Collects user response ratings per message.
     - 🔒 **Options Menu**: New chat, copy transcript, direct phone/WhatsApp handoff, and privacy notice.

3. **Live Installation Verification Crawler (`/api/verify-install`)**:
   - Real crawler that requests the client's official website URL, inspects the HTML for `<script src=".../widget.js" data-assistant-id="..." defer></script>`.
   - Never claims installation is verified unless the script tag is physically verified on their site.
   - Provides clear diagnostic status codes and troubleshooting steps.

4. **Executive Client Pitch Demo Overlay (`/demo/{slug}`)**:
   - Loads the prospective client's actual live website in the background iframe (e.g. `prakruthiholidays.com`, `many2go.in`, `traveolla.com`, etc.).
   - Floats that client's branded AI concierge in the corner with a top Presenter Control Bar, multi-client switcher dropdown, and live slide-over CRM drawer for sales calls.

5. **Standalone Hosted Chat Portal (`/c/{slug}`)**:
   - Dedicated full-screen white-label web chat page for clients who want a direct link or QR code instead of embedding on a website.

6. **Super-Admin Command Center (`/admin`)**:
   - **30-Second Client Onboarding**: Add new agencies with custom colors, logo, welcome greeting, knowledge base, and webhook URL.
   - Quick template presets for top prospective travel agencies.
   - Real-time KPI counter: Active Agencies, Verified Installs, Total Leads, and Conversion Rate.
   - Unified Leads Inbox with live search, filtering by client agency, and one-click **CSV Export**.

---

## 📁 Architecture Overview

```
prakruthi-ai-concierge/
├── main.py                  # Central FastAPI microservice & multi-tenant routing
├── database.py              # SQLite WAL multi-tenant data layer & schema migrations
├── tenants.py               # Tenant configurations & automatic database seeding
├── ai_engine.py             # Multi-tenant Gemini 3.5 Flash-Lite reasoning & extraction
├── static/
│   ├── widget.js            # Universal Shadow DOM embeddable widget (v3.2.0)
│   ├── admin.html           # Devlancer Super-Admin Command Center & CRM
│   ├── demo.html            # Executive live website pitch overlay
│   └── standalone.html      # Hosted standalone client chat (/c/{slug})
├── test_embed.html          # Simulated 3rd-party customer website embedding widget
├── test_suite.py            # Comprehensive platform API test suite
├── test_crm_sync.py         # Google Apps Script CRM webhook connectivity tester
├── requirements.txt         # Dependencies
├── .env                     # API credentials
└── README.md                # Platform documentation
```

---

## 🏢 Pre-Seeded Holiday Agencies (Ready to Pitch)

The platform comes pre-seeded with 10 high-profile travel agencies from your prospective client target list:

| Agency | Focus & Differentiator | Pitch Demo URL | Standalone URL | Assistant ID |
| :--- | :--- | :--- | :--- | :--- |
| **Prakruthi Holidays** | Senior Citizen & Family Tours (Bengaluru) | [`/demo/prakruthi-holidays`](http://localhost:8000/demo/prakruthi-holidays) | [`/c/prakruthi-holidays`](http://localhost:8000/c/prakruthi-holidays) | `asst_prakruthi_kammanahalli` |
| **Many2Go Holidays** | Curated Fixed Departures & Europe Tours | [`/demo/many2go-holidays`](http://localhost:8000/demo/many2go-holidays) | [`/c/many2go-holidays`](http://localhost:8000/c/many2go-holidays) | `asst_many2go_holidays` |
| **Traveolla Holidays** | Luxury Honeymoons & Bali Private Villas | [`/demo/traveolla-holidays`](http://localhost:8000/demo/traveolla-holidays) | [`/c/traveolla-holidays`](http://localhost:8000/c/traveolla-holidays) | `asst_traveolla_vacations` |
| **RoamEaze** | Experiential Millennial Adventure & Treks | [`/demo/roameaze`](http://localhost:8000/demo/roameaze) | [`/c/roameaze`](http://localhost:8000/c/roameaze) | `asst_roameaze_travel` |
| **Prestige Holidays 4U**| Bespoke Luxury Worldwide & Cruises | [`/demo/prestige-holidays-4u`](http://localhost:8000/demo/prestige-holidays-4u) | [`/c/prestige-holidays-4u`](http://localhost:8000/c/prestige-holidays-4u) | `asst_prestige_holidays` |
| **HolidayTadka** | Affordable Family Domestic & International | [`/demo/holidaytadka`](http://localhost:8000/demo/holidaytadka) | [`/c/holidaytadka`](http://localhost:8000/c/holidaytadka) | `asst_holidaytadka_tours` |
| **eKashmir Tour Package**| Kashmir Houseboats, Gondola & Valleys | [`/demo/ekashmir-tour-package`](http://localhost:8000/demo/ekashmir-tour-package) | [`/c/ekashmir-tour-package`](http://localhost:8000/c/ekashmir-tour-package) | `asst_ekashmir_tours` |
| **AdventureHive** | High-Altitude Treks, Rafting & Safaris | [`/demo/adventurehive`](http://localhost:8000/demo/adventurehive) | [`/c/adventurehive`](http://localhost:8000/c/adventurehive) | `asst_adventurehive_expeditions` |
| **Destico** | Corporate MICE Offsites & Group Retreats | [`/demo/destico`](http://localhost:8000/demo/destico) | [`/c/destico`](http://localhost:8000/c/destico) | `asst_destico_travel` |
| **TrueYatri** | Sacred Pilgrimages (Char Dham, Ayodhya, Kashi) | [`/demo/trueyatri`](http://localhost:8000/demo/trueyatri) | [`/c/trueyatri`](http://localhost:8000/c/trueyatri) | `asst_trueyatri_spiritual` |

---

## 🚀 Running the Platform

Ensure the server is running on port 8000:

```bash
cd /Users/bhatsakib/Desktop/prakruthi-ai-concierge
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Key URLs:
- **Devlancer Super-Admin Portal**: **[http://localhost:8000/admin](http://localhost:8000/admin)**
- **Simulated 3rd-Party Embed Test**: **[http://localhost:8000/test-embed](http://localhost:8000/test-embed)**
- **Executive Pitch Demo (Many2Go)**: **[http://localhost:8000/demo/many2go-holidays](http://localhost:8000/demo/many2go-holidays)**
- **Executive Pitch Demo (Prakruthi)**: **[http://localhost:8000/demo/prakruthi-holidays](http://localhost:8000/demo/prakruthi-holidays)**
- **Hosted Standalone Chat**: **[http://localhost:8000/c/many2go-holidays](http://localhost:8000/c/many2go-holidays)**

---

## 🧪 Automated Testing

Run the automated platform test suite anytime:

```bash
.venv/bin/python test_suite.py
```
