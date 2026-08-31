# AI Revenue Recovery Agent: Mandate Retry Sequencer + Promise-to-Pay Loop

> An intelligent, bounded, and explainable AI-powered recovery agent that recovers failed recurring payment mandates (UPI Autopay, e-NACH) through smart retry sequencing and Hinglish conversational Promise-to-Pay negotiations.

---

## 📌 Executive Summary

Recurring payment mandate failures in India (UPI Autopay, e-NACH, card mandates) create massive revenue leakage for subscription, SaaS, OTT, and lending/EMI businesses. Merchants typically face two flawed extremes:
1. **Blind Retries:** Retrying on a rigid schedule, exhausting retry attempts, incurring bank bounce charges, and risking blacklisting by NPCI/banks.
2. **Silent Failure:** Inaction, resulting in permanent customer churn and lost revenue.

**This project builds a closed-loop, bounded recovery system:**
$$\text{Detect Failure} \longrightarrow \text{Diagnose Reason} \longrightarrow \text{Choose Bounded Action} \longrightarrow \text{Execute Intervention} \longrightarrow \text{Track Outcome} \longrightarrow \text{Escalate Compliantly}$$

---

## 🏛️ Core Architectural Principle: Bounded & Explainable AI

Unlike naive AI projects that give an LLM unchecked control over financial transactions, this system follows an **enterprise-grade, compliance-first architecture**:

1. **Deterministic Decision Engine (Code-Based):** 
   - Strict banking rules enforce safety bounds (max 3 retries, salary-cycle timing, max 1 grace nudge, immediate escalation for closed accounts).
   - The LLM **never** decides whether to charge or escalate.
2. **Gated LLM Utilization:**
   - **Hinglish Date Parsing:** Interpreting natural customer language and extracting structured payment commitment dates.
   - **Audit Explainability:** Generating human-readable rationale for every decision logged in the compliance audit trail.
3. **Virtual Time Machine (Fast-Forward Clock):**
   - Allows instant demonstration of multi-day workflows (retries maturing, payment links expiring, grace nudges firing) without waiting days.

---

## 📂 Documentation Directory (`docs/`)

Explore the comprehensive documentation breakdown:

| Document | Description |
| :--- | :--- |
| [01. Overview & Architecture](docs/01_overview_and_architecture.md) | High-level system architecture, component diagrams, and core philosophy. |
| [02. Features & Specifications](docs/02_features_and_specifications.md) | Complete list of functional requirements, UI views, and system features. |
| [03. Decision Engine & Rules](docs/03_decision_engine_and_rules.md) | Deterministic policy matrix, retry scheduling math, and bounds safety limits. |
| [04. LLM & Promise-to-Pay Flow](docs/04_llm_and_ptp_flow.md) | Hinglish prompt engineering, ambiguity handling, and grace nudge stopping rules. |
| [05. Data Models & Database](docs/05_data_models_and_database.md) | Complete SQLite schema, entity-relationship diagrams, and state transitions. |
| [06. API Reference](docs/06_api_reference.md) | FastAPI endpoint contracts, request/response models, and webhook signatures. |
| [07. Setup & Demo Guide](docs/07_setup_and_demo_guide.md) | Local installation instructions, environment config, and 4-minute demo pitch script. |

---

## 🛠️ Technology Stack

* **Backend:** Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy / SQLModel
* **Database:** SQLite (file-based, zero-config, ACID-compliant)
* **Frontend:** React 18 (Vite), Tailwind CSS / Vanilla CSS, Lucide Icons
* **LLM Engine:** Multi-provider support (OpenAI / Anthropic Claude / Google Gemini / Local Ollama / Offline Mock Provider)
* **Payment Gateway:** Razorpay Test-Mode APIs & Webhook Simulator

---

## ⚡ Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit the dashboard at `http://localhost:5173`.
