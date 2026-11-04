# DocAI: Application Execution & Runbook Guide
### AI-Based Fake Identity & Document Screening System with Blockchain & Cybersecurity

---

## Table of Contents
1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Prerequisites & System Requirements](#2-prerequisites--system-requirements)
3. [Quick Start Execution (Recommended)](#3-quick-start-execution-recommended)
   - [Step 1: Check & Free Ports (3000 & 8000)](#step-1-check--free-ports-3000--8000)
   - [Step 2: Start the FastAPI Backend](#step-2-start-the-fastapi-backend)
   - [Step 3: Start the Next.js Frontend](#step-3-start-the-nextjs-frontend)
4. [Running on Alternative Ports (When Ports 8000/3000 are Busy)](#4-running-on-alternative-ports-when-ports-80003000-are-busy)
5. [Accessing the Application & User Roles](#5-accessing-the-application--user-roles)
6. [Interactive Feature Walkthrough](#6-interactive-feature-walkthrough)
   - [A. Seeding Demo Data (1-Click)](#a-seeding-demo-data-1-click)
   - [B. Running a New Identity Screening](#b-running-a-new-identity-screening)
   - [C. Investigating Forensics & Tampering Analysis](#c-investigating-forensics--tampering-analysis)
   - [D. Biometric Face Verification](#d-biometric-face-verification)
   - [E. Blockchain Verification (Zero-PII Proofs)](#e-blockchain-verification-zero-pii-proofs)
   - [F. Hash-Chained Audit Ledger Inspection](#f-hash-chained-audit-ledger-inspection)
   - [G. Downloading PDF Screening Reports](#g-downloading-pdf-screening-reports)
7. [Automated Verification & Unit Tests](#7-automated-verification--unit-tests)
8. [Docker Compose Deployment](#8-docker-compose-deployment)
9. [Troubleshooting & FAQs](#9-troubleshooting--faqs)

---

## 1. System Overview & Architecture

DocAI is a high-assurance identity screening platform. The application runs as two coordinated services:

```
                    ┌───────────────────────────────────────┐
                    │       Next.js 14 Web Frontend         │
                    │         http://localhost:3000         │
                    └───────────────────┬───────────────────┘
                                        │ REST API (JWT)
                                        ▼
                    ┌───────────────────────────────────────┐
                    │        FastAPI Backend Engine         │
                    │        http://127.0.0.1:8000          │
                    │       (Swagger: /docs, /health)       │
                    └───────────────────┬───────────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
   ┌───────────────┐            ┌───────────────┐            ┌───────────────┐
   │ SQLite / DB   │            │ AI Forensics  │            │ EVM / Sepolia │
   │ Data & Audit  │            │ OCR / Vision  │            │ Blockchain    │
   └───────────────┘            └───────────────┘            └───────────────┘
```

---

## 2. Prerequisites & System Requirements

Ensure the following tools are installed on your machine:

| Component | Minimum Version | Verified Version | Check Command |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11+ | Python 3.14.6 | `python --version` |
| **Node.js** | 18+ | Node.js v24.15.0 | `node -v` |
| **npm** | 9+ | npm 11.12.1 | `npm -v` |
| **Git** | 2.x | Git 2.45+ | `git --version` |

---

## 3. Quick Start Execution (Recommended)

### Step 1: Check & Free Ports (3000 & 8000)

If you previously ran an application on port `8000` or `3000`, terminate them before launching DocAI:

#### On Windows (PowerShell):
```powershell
# 1. Check which processes are occupying ports 8000 and 3000
Get-NetTCPConnection -LocalPort 8000, 3000 -ErrorAction SilentlyContinue | Select-Object LocalPort, State, OwningProcess

# 2. Terminate the blocking processes automatically
Get-NetTCPConnection -LocalPort 8000, 3000 -ErrorAction SilentlyContinue | ForEach-Object { 
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue 
}
```

#### On Linux / macOS (Bash):
```bash
# Terminate processes on ports 8000 and 3000
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true
```

---

### Step 2: Start the FastAPI Backend

Open a **dedicated terminal window**:

```powershell
# Navigate to the project root directory
cd e:\docAI

# Activate virtual environment (if using venv, optional)
# .\venv\Scripts\Activate.ps1

# Install Python requirements (first time only)
python -m pip install -r requirements.txt

# Start the FastAPI backend server
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

#### Verification:
- **API Status**: Open [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
  - Expected response: `{"status": "healthy", "service": "AI Fake Identity & Document Screening System", ...}`
- **Interactive Swagger Documentation**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Step 3: Start the Next.js Frontend

Open a **second terminal window**:

```powershell
# Navigate to the frontend directory
cd e:\docAI\frontend

# Install dependencies (first time only)
npm install

# Start Next.js development server
npm run dev
```

#### Verification:
- Open your browser to: **[http://localhost:3000](http://localhost:3000)**
- If your browser displays cached content from an older app, press **`Ctrl + F5`** or **`Ctrl + Shift + R`** to force refresh.

---

## 4. Running on Alternative Ports (When Ports 8000/3000 are Busy)

If you have another critical application that must remain running on ports 8000 or 3000, you can run DocAI on ports **8001** and **3001**:

### 1. Start Backend on Port 8001:
```powershell
cd e:\docAI
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8001
```

### 2. Start Frontend on Port 3001 (pointing to 8001):
```powershell
cd e:\docAI\frontend
$env:BACKEND_URL="http://127.0.0.1:8001"
npm run dev -- -p 3001
```
Open **[http://localhost:3001](http://localhost:3001)** in your browser.

---

## 5. Accessing the Application & User Roles

DocAI implements strict Role-Based Access Control (RBAC). Three seeded accounts are available:

| Role | Email | Password | Allowed Actions |
| :--- | :--- | :--- | :--- |
| **Screening Officer** | `officer@docai.gov` | `Officer@123456` | Intake cases, upload documents, run AI screening pipeline, view case details. |
| **Supervisor** | `supervisor@docai.gov` | `Supervisor@123456` | Review escalated cases, approve/reject flags, audit log review, risk threshold oversight. |
| **Administrator** | `admin@docai.gov` | `Admin@123456` | Full system governance, system health, risk engine parameter configuration, security audits. |

*Quick Tip: The login screen contains **1-click quick-fill buttons** for each role.*

---

## 6. Interactive Feature Walkthrough

### A. Seeding Demo Data (1-Click)
1. Sign in as `officer@docai.gov` or `admin@docai.gov`.
2. On the top navigation bar or Dashboard, click the **"Load Demo Dataset"** button.
3. This creates three pre-configured synthetic cases:
   - **Case 1: Verified Traveler (John Doe)** — Low risk (`15/100`), genuine passport + visa match, biometric face match (`96%`).
   - **Case 2: Suspicious Visa (Jane Smith)** — High risk (`68/100`), document number mismatch, photo border tampering detected.
   - **Case 3: Critical Fraud Ring (Alex Rivera)** — Critical risk (`89/100`), expired travel document, live selfie face mismatch (`38%`).

---

### B. Running a New Identity Screening
1. Click **"New Screening"** in the sidebar.
2. Complete the step-by-step intake wizard:
   - **Step 1: Traveler Details** — Name, DOB, Nationality.
   - **Step 2: Document Upload** — Upload Passport / Visa image (`PNG`, `JPG`, `WEBP`, or `PDF`).
   - **Step 3: Live Biometric Selfie** — Upload the applicant's live camera photo.
3. Click **"Run Full AI Screening"**.
4. The system executes:
   - ICAO Doc 9303 MRZ OCR extraction & cross-field checksum parsing.
   - Error Level Analysis (ELA) & gradient noise tampering inspection.
   - 1:1 Biometric face verification against the document photo holder.
   - Cross-document validation (e.g. Passport # vs Visa #).
   - Weighted explainable risk score calculation.
   - Cryptographic SHA-256 binary hashing and blockchain anchoring.

---

### C. Investigating Forensics & Tampering Analysis
1. Open any case from the **"Cases"** page.
2. Navigate to the **"Forensics"** tab.
3. The interactive viewer displays:
   - **Original Document**: Uploaded image with high-resolution inspection.
   - **Error Level Analysis (ELA) Heatmap**: Highlighted compression anomalies indicating spliced text or swapped portraits.
   - **Edge Noise & Laplacian Map**: Discrepancies in high-frequency noise between the portrait quadrant and security background.
   - **Metadata Inspection**: Identification of editing software fingerprints (e.g. Adobe Photoshop, GIMP, Canva).

---

### D. Biometric Face Verification
1. Within the case dossier, inspect the **"Biometric Verification"** panel.
2. The engine displays:
   - Document crop portrait vs. Live selfie capture.
   - Structural feature correlation percentage.
   - Multi-channel HSV skin-tone distribution histogram.
   - Continuous score (0-100%) and advisory flag: `MATCH`, `MISMATCH`, or `UNABLE TO VERIFY`.

---

### E. Blockchain Verification (Zero-PII Proofs)
1. Go to **"Blockchain"** in the sidebar (or click the verified badge on any case).
2. Inspect the on-chain proof:
   - **Case Hash**: Keccak-256 digest of the case identifier.
   - **Document Hash**: SHA-256 fingerprint of the binary document file.
   - **Verification Hash**: Cryptographic state of the AI screening output.
   - **Risk Classification**: Transparent risk score anchored immutably.
   - **Explorer Link / Status**: Verified on Ethereum Sepolia or Local EVM Sandbox.
3. Paste any document hash to verify real-time cryptographic integrity.

---

### F. Hash-Chained Audit Ledger Inspection
1. Navigate to **"Audit Trail"** in the navigation bar.
2. Every action (Upload, AI Analysis, Risk Determination, Officer Decision) is chained with:
   $$\text{Entry Hash} = \text{SHA-256}(\text{Prev Hash} + \text{Seq} + \text{Case ID} + \text{User ID} + \text{Action} + \text{Timestamp})$$
3. Any attempt to modify a database entry invalidates subsequent cryptographic signatures.

---

### G. Downloading PDF Screening Reports
1. In any case dossier, click the **"Export Official PDF Report"** button.
2. An official, watermarked security dossier is generated containing:
   - Official Case ID, Officer metadata, and timestamp.
   - Itemized risk penalty breakdown.
   - Biometric similarity and forensic anomaly tables.
   - Blockchain proof transaction hash and QR/digital verification digest.

---

## 7. Automated Verification & Unit Tests

Run the full end-to-end test suite to verify all subsystem components:

### Backend Test Suite (Pytest):
```powershell
cd e:\docAI
python -m pytest backend/tests/ -v
```
**Test Coverage Includes:**
- `test_auth_and_rbac`: JWT token generation, unauthorized access blocking, role separation.
- `test_ai_pipeline_full`: OCR parsing, tampering analysis, face verifier, risk calculation.
- `test_blockchain_service`: Zero-PII hashing, deterministic EVM registry, state integrity.
- `test_audit_chain_integrity`: Hash chaining, tamper detection, sequence preservation.
- `test_pdf_generation`: ReportLab PDF generation and file structure validation.

### Frontend Production Build Test:
```powershell
cd e:\docAI\frontend
npm run build
```
*(Confirms TypeScript type-safety and compiles all 12 application routes without errors).*

---

## 8. Docker Compose Deployment

To deploy DocAI as an isolated containerized stack with PostgreSQL:

```bash
# Build and run all services
docker-compose up --build -d

# View real-time logs
docker-compose logs -f

# Stop the containers
docker-compose down
```

**Services Deployed:**
- **Frontend**: `http://localhost:3000`
- **FastAPI Backend**: `http://localhost:8000`
- **PostgreSQL 16**: `localhost:5432`

---

## 9. Troubleshooting & FAQs

### Q1: `Error: listen EADDRINUSE: address already in use :::3000`
**Cause**: Another application or an orphaned Node.js process is holding port 3000.  
**Fix**:
```powershell
# Kill the process on port 3000
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

---

### Q2: `Uvicorn failed to bind to 127.0.0.1:8000: [WinError 10048]`
**Cause**: A previous Python or Uvicorn process is still running.  
**Fix**:
```powershell
# Kill the process on port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

---

### Q3: Why does my browser show an older app when I open `localhost:3000`?
**Cause**: The browser has cached the service worker or JavaScript bundle of an application previously hosted on port 3000.  
**Fix**:
1. Open Chrome / Edge / Firefox.
2. Press **`Ctrl + Shift + Delete`** and clear cached images and files, or:
3. Open an **Incognito / Private Window** (`Ctrl + Shift + N`) and visit `http://localhost:3000/login`.

---

### Q4: Are real passports or citizen data uploaded to the blockchain?
**No**. The system follows **Zero-PII On-Chain Compliance**. Only SHA-256 mathematical hashes and risk scores are anchored. No personal names, document photos, or biometric profiles ever touch the blockchain.
