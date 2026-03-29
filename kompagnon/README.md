# 🚀 KOMPAGNON Automation System

Complete WordPress website automation for German handcraft businesses.

- **2.000€ fixed price**
- **14 business days delivery**
- **KI-powered (Claude API)**
- **Real-time margin tracking** (target: 78%)
- **Post-launch automation** (emails, reviews, upsells)

---

## 📋 Quick Start (5 Steps)

### 1. Clone & Setup
```bash
git clone https://github.com/your-org/kompagnon.git
cd kompagnon
bash setup.sh
```

### 2. Configure Environment
```bash
cd kompagnon
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Backend
```bash
cd backend
source ../venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Frontend
```bash
cd ../frontend
npm install
npm start
```

### 5. Access
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Health**: http://localhost:8000/health

---

## 🏗️ Architecture

### Backend (Python/FastAPI)
```
backend/
├── main.py                 # Entry point, scheduler startup
├── database.py             # SQLAlchemy models (7 models)
├── config.py               # Environment configuration
├── routers/                # 28+ API endpoints
│   ├── leads.py            # Lead pipeline
│   ├── projects.py         # 7-phase workflow
│   ├── agents.py           # KI agent execution
│   ├── customers.py        # Post-project management
│   └── automations.py      # Dashboard, alerts, triggers
├── agents/                 # 5 KI agents (Claude API)
│   ├── lead_analyst.py     # Website analysis
│   ├── content_writer.py   # Hero, About, FAQ, Meta-Tags
│   ├── seo_geo_agent.py    # JSON-LD, robots.txt, sitemap
│   ├── qa_agent.py         # QA checklist, go-live decision
│   └── review_agent.py     # Review requests + phone scripts
├── services/
│   ├── margin_calculator.py # Real-time margin (78% target)
│   ├── email_service.py    # SMTP + logging
│   └── link_checker.py     # Broken link detection
└── automations/
    ├── scheduler.py        # APScheduler with 10+ jobs
    └── email_templates.py  # 8 email templates (German)
```

### Frontend (React/Tailwind)
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx        # KPI overview, alerts
│   │   ├── LeadPipeline.jsx     # Lead management
│   │   ├── ProjectDetail.jsx    # 7-phase tracker
│   │   ├── Checklists.jsx       # QA checklists
│   │   └── Customers.jsx        # Upsell tracking
│   ├── components/
│   │   ├── MarginBadge.jsx      # Green/Yellow/Red status
│   │   ├── PhaseTracker.jsx     # Visual phase progress
│   │   ├── AgentPanel.jsx       # KI agent output viewer
│   │   └── AlertBanner.jsx      # Critical alerts
│   └── App.jsx
```

### Database (SQLite → Postgres-ready)
- **Lead**: Sales pipeline (status: new → won/lost)
- **Project**: 7-phase workflow (phase_1 → completed)
- **ProjectChecklist**: 54 items across 7 phases
- **Communication**: All emails/calls logged with templates
- **AutomationLog**: Audit trail of all triggers
- **Customer**: Post-project upsells & touchpoints
- **TimeTracking**: Hours logged by person/phase (margin calc)

---

## 🤖 The 5 KI Agents

### 1. **LeadAnalystAgent**
Analyzes business website → scores (0-100) for sales team
- Website age, mobile score, performance score
- SSL check, impressum detection, geo visibility
- Top 3 issues + sales pitch template

### 2. **ContentWriterAgent**
Generates conversion-focused German website copy
- Hero headline (max 8 words)
- About text (150 words, I-perspective)
- Service descriptions (80 words each)
- FAQ (5+ items), Meta tags (title/description)
- Local CTA with city name

### 3. **SeoGeoAgent**
Creates complete local SEO setup
- LocalBusiness, FAQ, Service, Breadcrumb JSON-LD
- robots.txt + sitemap.xml template
- Geo-readiness score (0-100)
- 5 SEO recommendations

### 4. **QaAgent**
Conducts QA review against checklists + tests
- Evaluates PageSpeed, links, SSL, mobile, legal compliance
- Critical failures vs. warnings
- **Go-live recommendation** (yes/no)
- 3-sentence client presentation

### 5. **ReviewAgent**
Generates personalized review requests
- Email subject + 150-word body (personal, not generic)
- Phone script with tactics (what to say/avoid)
- Support for Google + ProvenExpert

---

## ⚙️ Automation Workflows

### Daily Jobs (cron)
- **08:00**: Check overdue phases (> 2 days stuck)
- **09:00**: Check missing materials (> 5 days)
- **10:00**: Recalculate all project margins

### Post-Go-Live Sequence
- **Day 1**: Congratulations email (automated)
- **Day 5**: Functionality check + visitor stats
- **Day 14**: Status report + optimization suggestions
- **Day 21**: Review request (if not received)
- **Day 30**:
  - GEO-check email
  - Upsell offer (if no upsell yet)

### Event-Based Triggers
- Payment received → Welcome email + Phase 2 kickoff
- Customer approval → Go-live prep email
- Go-live → Schedule all follow-up jobs

---

## 💰 Margin Tracking (Real-Time)

```
Fixed Price: €2.000
- Human Hours: 8.5h × €45 = €382,50
- AI Tool Costs: €50
= Total Costs: €432,50
= Margin: €1.567,50 (78%)

Status:
🟢 Green (≥70%)
🟡 Yellow (60-70%)
🔴 Red (<60%) ← Alert!
```

**Dashboard shows:**
- Active projects count
- Average margin %
- Projects at target (≥70%)
- Projects at risk (<60%)

---

## 📊 API Endpoints (28+)

### Leads (/api/leads)
- `POST /` - Create lead
- `GET /` - List leads
- `GET /{id}` - Lead detail
- `PATCH /{id}` - Update lead
- `POST /{id}/analyze` - Run LeadAnalystAgent
- `POST /{id}/convert` - Convert to project

### Projects (/api/projects)
- `GET /` - List projects
- `GET /{id}` - Project detail
- `PATCH /{id}/phase` - Change phase
- `POST /{id}/time` - Log hours
- `GET /{id}/checklist` - Get checklist
- `PATCH /{id}/checklist/{item_key}` - Check off item
- `GET /{id}/margin` - Get real-time margin
- `POST /{id}/trigger` - Manual automation trigger

### Agents (/api/agents)
- `POST /{project_id}/content` - Run ContentWriterAgent
- `POST /{project_id}/seo` - Run SeoGeoAgent
- `POST /{project_id}/qa` - Run QaAgent
- `POST /{project_id}/review` - Run ReviewAgent

### Customers (/api/customers)
- `GET /` - List customers
- `GET /{id}` - Customer detail
- `PATCH /{id}` - Update upsell status
- `POST /{project_id}/create` - Create customer at go-live

### Dashboard (/api)
- `GET /dashboard/kpis` - KPI data
- `GET /dashboard/alerts` - Active alerts
- `GET /dashboard/projects-by-phase` - Kanban view
- `GET /automations/jobs` - Scheduled jobs
- `POST /automations/test-email` - SMTP test

---

## 🔐 Security

- ✅ HTTPS-ready (SSL cert on deployment)
- ✅ CORS restricted to whitelisted origins
- ✅ Database password hash (future: implement for users)
- ✅ API keys in environment variables (never committed)
- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (SQLAlchemy ORM)

---

## 🚢 Deployment

### Local Development
```bash
bash setup.sh
cd backend && uvicorn main:app --reload
```

### VPS/Production
```bash
# Install
git clone ...
bash setup.sh
# Configure
nano .env  # Set ENVIRONMENT=production
# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Docker (Optional)
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
```

---

## 📝 Database Schema (7 Models)

| Model | Fields | Key Relations |
|-------|--------|---|
| **Lead** | id, company_name, contact_name, phone, email, website_url, city, trade, status, analysis_score, geo_score | → Project (1:many) |
| **Project** | id, lead_id, status (phase_1-7), start_date, fixed_price, actual_hours, margin_percent | → Checklist, Communication, Customer, TimeTracking |
| **ProjectChecklist** | id, project_id, phase (1-7), item_key, item_label, responsible (ki/human/both), is_critical, is_completed | → Project |
| **Communication** | id, project_id, type, direction, subject, body, is_automated, template_key | → Project |
| **AutomationLog** | id, project_id, automation_id, trigger_event, status, output_summary | → Project |
| **Customer** | id, project_id, next_touchpoint_date, upsell_status, upsell_package, recurring_revenue | → Project |
| **TimeTracking** | id, project_id, phase, logged_by, hours, activity_description | → Project |

---

## 🧪 Testing

```bash
# Run pytest
pytest backend/tests/ -v

# Test email service
curl -X POST "http://localhost:8000/api/automations/test-email?recipient=test@example.com"

# Check health
curl http://localhost:8000/health
```

---

## 📞 Support

- **Docs**: http://localhost:8000/docs (Swagger/OpenAPI)
- **Issues**: GitHub Issues
- **Email**: support@kompagnon.de

---

## 📄 License

Proprietary - KOMPAGNON GmbH

---

**Made with ❤️ for German handcraft businesses**
