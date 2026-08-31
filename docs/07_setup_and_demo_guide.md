# 07. Setup, Running & 4-Minute Demo Pitch Guide

## 1. Prerequisites & Environment Setup

### Required Tools
- **Python:** Version 3.10 or higher
- **Node.js:** Version 18 or higher (with `npm`)
- **Git**

---

## 2. Step-by-Step Installation

### 2.1 Backend Setup (FastAPI + SQLite)
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (Command Prompt):
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables
cp .env.example .env
```

#### Sample `.env` Configuration
```env
# Server
PORT=8000
HOST=127.0.0.1
DEBUG=True

# SQLite
DATABASE_URL=sqlite:///./revenue_recovery.db

# LLM Configuration (Optional: Mock engine is built-in if no key is provided)
OPENAI_API_KEY=your_openai_key_here
# or GEMINI_API_KEY / ANTHROPIC_API_KEY

# Razorpay Test Mode (Optional: Mock payloads work out of the box)
RAZORPAY_KEY_ID=rzp_test_xxxx
RAZORPAY_KEY_SECRET=xxxx
```

```bash
# Start backend dev server
uvicorn app.main:app --reload --port 8000
```
Backend will be live at: `http://localhost:8000` (Swagger UI at `http://localhost:8000/docs`).

---

### 2.2 Frontend Setup (React + Vite + Tailwind CSS)
```bash
# In a separate terminal, navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend will be live at: `http://localhost:5173`.

---

## 3. The 4-Minute Winning Demo Pitch Script

Use this exact structure during hackathon presentations or investor/recruiter demos:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        4-MINUTE DEMO BREAKDOWN                         │
│                                                                        │
│  [0:00 - 0:30] Problem: Revenue leakage & blind retries               │
│  [0:30 - 1:30] Run Batch & Fast-Forward Clock (Watch recovery climb)   │
│  [1:30 - 2:30] Live Hinglish Roleplay Chat & Ambiguity Clarification  │
│  [2:30 - 3:15] Grace Nudge & Clean Human Escalation Stopping Rule      │
│  [3:15 - 4:00] Audit Trail Inspection & Closing Numbers               │
└────────────────────────────────────────────────────────────────────────┘
```

### [0:00 - 0:30] The Hook & Problem Statement
* *"Every day, subscription and lending businesses in India lose millions when UPI Autopay and e-NACH mandates fail. Most businesses do one of two things: they either retry blindly on fixed days—wasting bounce fees and getting blacklisted—or they give up silently."*
* *"Today, we present the AI Revenue Recovery Agent: a bounded, explainable system that retries intelligently and negotiates Promise-to-Pay in natural Hinglish."*

### [0:30 - 1:30] The Batch Run & Virtual Time-Travel
1. Click **"Run Batch (15 Cases)"** on the dashboard.
2. Highlight: *"Notice that the system didn't schedule retries for tomorrow. For Rahul whose salary is credited on the 1st, it scheduled the retry for September 3rd—2 days post-payday when liquidity exists."*
3. Click **"+2 Days"** on the Virtual Clock controller.
4. Watch the table update: 4 retries succeed, and the **₹ Recovered** counter climbs from ₹0 to ₹14,990.

### [1:30 - 2:30] Live Hinglish Chat & Ambiguity Gate
1. Click on a case with `mandate_expired` to open the **Promise-to-Pay Chat Drawer**.
2. Type an ambiguous customer reply: *"Bhai salary aane pe deta hu"* (I'll give when salary arrives).
3. Point out: *"Notice the agent does not hallucinate a date. It triggers our single clarification gate:"*
   - Bot replies: *"Dhanyawad! Kya aap koi specific date bata sakte hain jaise 5th September?"*
4. Type: *"Haan 5th September pakka"*.
5. Watch the extracted badge appear (`2026-09-05`) and the dynamic Razorpay payment link generate instantly.

### [2:30 - 3:15] Demonstrating the Stopping Rule (Compliance)
1. Advance the Virtual Clock to **September 6th** (1 day past the promised date).
2. Show the single **Grace Nudge** triggered automatically.
3. Advance the clock another day without payment:
4. Point out: *"Here is our stopping rule in action. The agent will never nag indefinitely. It permanently halts automated outreach and transitions the case cleanly to the Human Escalation Queue with the full conversation history."*

### [3:15 - 4:00] The Audit Trail & Wrap-Up
1. Open the **Case Audit Drill-Down Panel**.
2. Show the complete timeline: Initial Failure $\rightarrow$ Rule Execution $\rightarrow$ LLM Reasoning $\rightarrow$ Grace Nudge $\rightarrow$ Escalation.
3. Conclude: *"In 4 minutes, we demonstrated ₹28,400 recovered across our batch, zero unbounded LLM actions, and 100% auditable compliance. Thank you!"*
