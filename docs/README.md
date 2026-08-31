# Documentation Index - AI Revenue Recovery Agent

Welcome to the comprehensive documentation suite for the **AI Revenue Recovery Agent (Mandate Retry Sequencer + Promise-to-Pay Loop)**.

## 📚 Complete Document Library

1. **[01. Overview & System Architecture](01_overview_and_architecture.md)**
   - Problem definition (recurring mandate failure in India).
   - Core philosophy: Deterministic policy + Gated LLM + Immutable audit.
   - End-to-end architecture diagrams & subsystem interactions.

2. **[02. Features & Functional Specifications](02_features_and_specifications.md)**
   - 15 Pre-seeded batch failure scenarios.
   - Dialogue state machine for Promise-to-Pay (PTP).
   - UI screen wireframes & layout breakdown.

3. **[03. Decision Engine & Deterministic Rules](03_decision_engine_and_rules.md)**
   - Complete policy matrix for decline codes (`insufficient_funds`, `bank_timeout`, `mandate_expired`, `account_closed`).
   - Salary cycle retry arithmetic (Salary Day $+ 2$ days buffer).
   - Bounded safety caps & stopping rules.

4. **[04. LLM Integration & Promise-to-Pay Flow](04_llm_and_ptp_flow.md)**
   - Hinglish conversational prompt engineering.
   - Few-shot NLU date parsing with ambiguity resolution gate.
   - Grace nudge logic and compliance audit reasoning prompt.

5. **[05. Data Models & Database Architecture](05_data_models_and_database.md)**
   - SQLite ER Diagram.
   - SQLAlchemy / SQLModel table schemas (`customers`, `mandate_attempts`, `promises_to_pay`, `audit_log`, `conversation_log`).

6. **[06. API Reference & Gateway Integration](06_api_reference.md)**
   - FastAPI REST API specs (`/api/batch`, `/api/cases`, `/api/clock`, `/api/chat`, `/api/escalation`).
   - Razorpay test webhook & mock engine payload formats.

7. **[07. Setup, Running & Demo Pitch Guide](07_setup_and_demo_guide.md)**
   - Step-by-step local installation (Python, FastAPI, React, Vite, SQLite).
   - The 4-minute winning demo pitch script with exact timestamps and actions.
