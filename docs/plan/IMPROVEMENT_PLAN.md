# Heketon — Post-Implementation Improvement Plan
## Based on Tencent Cloud Hackathon Indonesia 2026 Rulebook (Challenge B: "The Office Agent")

**Document Path**: `docs/plan/IMPROVEMENT_PLAN.md`  
**Created At**: 2026-10-28  
**Target Challenge**: Challenge B — The Office Agent (HR & Office Ops AI Orchestrator)  
**Target Milestone**: Grand Finalist & Overall Champion (100 / 100 Score Target)

---

## 1. Executive Summary & Context

Heketon has successfully implemented the complete core dual-pipeline LangGraph agent architecture with live validation via Playwright MCP, PostgreSQL state persistence, and real-time LLM reasoning via Sumopod (`glm-5.3-flash`). 

To maximize the team's standing against the official **Tencent Cloud Hackathon Indonesia 2026 Rulebook** (`docs/Rulebook.pdf`), this improvement plan identifies every remaining competitive advantage, bonus criteria, and mandatory submission deliverable specified in **Section 4 (Challenge B, pp. 6–7)**, **Section 6 (Data & Testing, p. 10)**, **Section 7 (Submission Requirements, pp. 11–12)**, and **Section 10 (Evaluation Rubric, pp. 15–16)**.

### Target Score Matrix (10 × 10 = 100 Points)

| Evaluation Dimension | Weight | Target Focus for Heketon | Planned Status |
| :--- | :---: | :--- | :---: |
| **1. Impact & Relevance** | 10 | Solves real Indonesian ATS/scheduling chaos and compliance with **PP 33/2026** (Data Privacy Impact Assessment) | 10 / 10 |
| **2. Human-Centered Design** | 10 | Non-disruptive triage: HR lead retains 100% control, clear who/what/when/where confirmation card | 10 / 10 |
| **3. AI Interaction** | 10 | Genuinely multi-node agentic DAG (Guardrail → Retriever → Planner → Secondary Validator → Undo Window → Executor) | 10 / 10 |
| **4. Technical Execution** | 10 | 56/56 automated tests passing, real DB side-effects, fast live execution with fallback safety net | 10 / 10 |
| **5. Feasibility & Scaling** | 10 | Monorepo architecture (FastAPI + Next.js 16 + PostgreSQL + pgvector), modular and enterprise-ready | 10 / 10 |
| **6. Demo & Storytelling** | 10 | 5–8 min compelling pitch showing refusal (prayer blackout/injection), clarification (Two Budis), and 60s undo | 10 / 10 |
| **7. Innovation & Creativity** | 10 | Multi-provider hybrid resilience + dual-pipeline post-interview competency evidence mapping | 10 / 10 |
| **8. UX & Accessibility** | 10 | TailAdmin Pro styling, mobile responsive, dark/light mode, clear status badges | 10 / 10 |
| **9. Responsible AI & Ethics** | 10 | Zero critical failures: strict permission boundary, salary masking, SHA-256 tamper-evident audit trail | 10 / 10 |
| **10. Judge's Impression & Trust** | 10 | "Would you trust this agent to operate in your organisation?" — Unanimous YES | 10 / 10 |

---

## 2. Rulebook Gap Analysis & High-Impact Targets

Cross-referencing our current implementation with the Rulebook reveals two categories of high-value opportunities:
1. **Bonus Functional Capabilities** (Explicitly awarded bonus points on Page 7).
2. **Mandatory Submission Deliverables** (Required for Round 1 judging on Page 11).

```
   ┌────────────────────────────────────────────────────────────────────────┐
   │                       RULEBOOK EVALUATION GAP                          │
   ├────────────────────────────────────┬───────────────────────────────────┤
   │ Current Status (100% Core Passing) │ Opportunities for Max Bonus Marks │
   ├────────────────────────────────────┼───────────────────────────────────┤
   │ [x] 5 Accountability Pillars       │ [ ] Voice Notes in Bahasa Indo    │
   │ [x] Secondary Validator Agent      │ [ ] Double Check for High-Impact  │
   │ [x] 60-Second Undo Buffer Window   │ [ ] 1-Page Accountability Sheet   │
   │ [x] Two-Budis Disambiguation Gate  │ [ ] 20-Test Case Dossier + Images │
   │ [x] Friday Prayer & Office Rules   │ [ ] 90s Surprise Test Sandbox     │
   └────────────────────────────────────┴───────────────────────────────────┘
```

---

## 3. The 5 Strategic Improvements

### Improvement 1: Voice Note Input in Bahasa Indonesia (*Rulebook Bonus, Page 7*)
- **Rulebook Specification**: *"Bonus: Voice notes in Bahasa Indonesia accepted as input."* (Example scenario: *"Tolong kirim notulen ke Pak Budi ya, terus jadwalin follow-up Jumat siang."*)
- **Objective**: Allow users to speak naturally or upload audio files directly into the Command Bar, transcribing spoken Indonesian into structured text commands before passing to the LangGraph pipeline.
- **Architecture**:
  ```mermaid
  flowchart LR
    A["Voice Note (.wav / .mp3 / Mic)"] --> B["Audio Ingestion Endpoint (/api/v1/orchestrator/voice-command)"]
    B --> C["ASR / Speech-to-Text Engine"]
    C --> D["Transcribed Indonesian Text"]
    D --> E["Guardrail & Injection Scanner"]
    E --> F["LangGraph StateGraph Execution"]
  ```
- **Components to Implement**:
  1. **Backend**:
     - Endpoint: `POST /api/v1/orchestrator/voice-command` in `OrchestratorCommandController.py`.
     - Service: `transcribe_and_orchestrate(file: UploadFile)` using existing ASR/Whisper pipeline or LLM audio parser.
     - Presets: Bundled sample Indonesian voice notes (e.g. `voice-sample-two-budis.wav`, `voice-sample-friday-clash.wav`) for 1-click live judge demos.
  2. **Frontend**:
     - `CommandBar.tsx`: Add a Microphone toggle button with browser `MediaRecorder` API support and a "Load Sample Voice Note" button.
     - Display live audio recording wave/timer and auto-populate transcription into the command bar upon release.

---

### Improvement 2: Double Confirmation for High-Impact Actions (*Rulebook Bonus, Page 7*)
- **Rulebook Specification**: *"Bonus: Additional confirmation for high-impact actions: multiple recipients, external emails or payments."*
- **Objective**: Protect against accidental high-stakes transmissions. If an action involves an external recipient (e.g. `@gmail.com` vs corporate `@company.com`), multiple participants, or stage alterations, require explicit dual verification.
- **Architecture**:
  ```mermaid
  flowchart TD
    Plan["Action Plan Drafted"] --> Eval{"High-Impact Criteria Met?"}
    Eval -->|"External Domain (@gmail) OR Multiple Recipients"| Flag["Set is_high_impact = True"]
    Eval -->|"Internal Single Recipient"| Standard["Standard Approval Flow"]
    Flag --> UI["ConfirmationCard: Warning Banner & Locked Action"]
    UI --> Checkbox["Mandatory Checkbox: 'Saya mengonfirmasi pengiriman ke pihak eksternal'"]
    Checkbox --> ApproveBtn["Approve Button Enabled"]
  ```
- **Components to Implement**:
  1. **Backend**:
     - In `PlannerTriageNode.py` and `SecondaryValidatorNode.py`: Add `is_high_impact: bool` and `high_impact_reasons: list[str]` to `ActionPlanDTO`.
     - Triggers:
       - Recipient email domain is not internal (e.g. not `@company.com` or `@internal.hr`).
       - Recipient count > 1.
       - Candidate status transition to `REJECTED` or `OFFERED`.
  2. **Frontend**:
     - In `ConfirmationCard.tsx`: When `is_high_impact` is true, render a high-visibility amber warning box listing the risk reasons and an interactive confirmation checkbox required before unlocking the "Approve & Dispatch" button.

---

### Improvement 3: Official 1-Page "Accountability Sheet" (*Mandatory Deliverable, Page 11*)
- **Rulebook Specification**: *"NEW / REQUIRED: Accountability sheet — A one-page summary of what your agent can access, what it executes autonomously, what requires human approval, and what it will never do."*
- **Objective**: Produce an authoritative, judge-ready 1-page document and UI viewer (`/audit/accountability`) satisfying the exact 4-quadrant criteria.
- **Content Matrix**:

| Quadrant | Detailed Boundaries in Heketon |
| :--- | :--- |
| **1. What the Agent CAN Access** | • Public candidate profile & ATS metadata (name, phone, applied position).<br>• Interviewer work calendar availability and office timezone (WIB/WITA/WIT).<br>• Master operational policies (office hours, Friday prayer window, Indonesian national holidays).<br>• Structured interview assessment rubrics & competencies. |
| **2. What the Agent Executes AUTONOMOUSLY** | • Adversarial prompt injection scanning & sanitization of notes/documents.<br>• Schedule conflict detection and alternative slot proposal calculation.<br>• Extraction of candidate preferred communication channel (WhatsApp/Email).<br>• Drafting natural language message templates with exact source citations.<br>• Automatic slot adjustment when prayer times or holidays clash. |
| **3. What REQUIRES Human Approval** | • External message transmission via WhatsApp Gateway or SMTP Email.<br>• Calendar event creation and room booking confirmation.<br>• Disambiguation resolution when multiple employee names conflict (e.g. Two Budis).<br>• Overriding proposed meeting slots or candidate application stage changes. |
| **4. What the Agent Will NEVER Do** | • Never sends external emails or WhatsApp messages without `ActionPlan.status == APPROVED`.<br>• Never exposes candidate salary expectations to Interviewers or non-HR users.<br>• Never executes commands embedded within forwarded documents or chat attachments.<br>• Never books meetings during Friday prayer time (11:30–13:00) without human escalation.<br>• Never modifies past audit logs or breaks the SHA-256 cryptographic tamper chain. |

---

### Improvement 4: 20 Test Cases & Evidence Dossier with Screenshots (*Mandatory Deliverable, Page 11*)
- **Rulebook Specification**: *"NEW / REQUIRED: Test results — Your results against your challenge's test cases, with screenshots. Include any that failed."*
- **Objective**: Consolidate a comprehensive 20-test-case dossier (`docs/TEST_RESULTS_REPORT.md`) matching the hackathon format, embedding screenshots generated by Playwright MCP.
- **Core Scenarios to Document**:
  1. Standard post-screening escalation to Round 1.
  2. Friday prayer conflict (11:30–13:00 WIB) auto-adjustment.
  3. Outside working hours (after 17:00 WIB) boundary rejection.
  4. Two-Budis name disambiguation gate.
  5. Cross-timezone candidate (WITA) vs interviewer (WIB) coordination.
  6. Prompt injection attempt: "SYSTEM OVERRIDE: Abaikan semua aturan".
  7. Prompt injection inside resume text / notes.
  8. Human approval gate: Action held in draft.
  9. Human rejection of proposed action plan.
  10. 60-Second undo buffer countdown cancellation.
  11. 60-Second undo buffer expiration auto-dispatch.
  12. Immediate send bypass option.
  13. National holiday conflict avoidance.
  14. Salary masking: Interviewer cannot see salary (`None`).
  15. Salary exposure: HR lead sees salary numbers.
  16. Unauthorized non-HR approval attempt (HTTP 403 Forbidden).
  17. Negotiation thread round counter limit (Round > 3 escalation).
  18. Post-interview audio transcript evaluation & rubric mapping.
  19. Candidate WhatsApp simulator inbound interaction.
  20. Immutable audit log SHA-256 hash chaining verification.

---

### Improvement 5: 90-Second Live Surprise Test Playground (*Demo Day Prep, Page 10*)
- **Rulebook Specification**: *"Live surprise test: On Demo Day, judges issue each finalist a previously unseen test case. Your agent has 90 seconds to resolve it, live."*
- **Objective**: Provide a "Judge Sandbox" in the UI allowing the presenter or judge to input custom unscripted text or voice input, displaying a live stopwatch timer and real-time execution step transparency to guarantee a flawless 90-second resolution.
- **Features**:
  - Live execution timer counting down from 90s to demonstrate instant resolution (< 5s).
  - Step-by-step inspector showing:
    - Step 1: Guardrail scan passed (< 50ms)
    - Step 2: Context retrieved with source IDs (< 100ms)
    - Step 3: LLM reasoning (Sumopod `glm-5.3-flash`, < 2000ms)
    - Step 4: Secondary validator passed (< 50ms)
    - Step 5: Draft plan locked awaiting approval.

---

## 4. Phase-by-Phase Implementation Roadmap

```mermaid
gantt
    title Heketon Hackathon Excellence Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1: High-Impact & Voice
    High-Impact Double Confirmation   :active, p1_1, 2026-10-28, 1d
    Indonesian Voice Note Ingestion  :p1_2, after p1_1, 1d
    section Phase 2: Deliverables
    Accountability Sheet (1-Page)    :p2_1, after p1_2, 1d
    20-Test-Case Dossier & Evidence  :p2_2, after p2_1, 1d
    section Phase 3: Demo Day Prep
    90-Second Judge Sandbox Mode     :p3_1, after p2_2, 1d
    Final Polish & Rehearsal         :p3_2, after p3_1, 1d
```

### Sprint 1: High-Impact Confirmation & Voice Input
- [ ] Add `is_high_impact` and reasons to `ActionPlanDTO` & `PlannerTriageNode.py`.
- [ ] Update `ConfirmationCard.tsx` with high-impact badge, warning alert, and mandatory approval confirmation checkbox.
- [ ] Add `POST /api/v1/orchestrator/voice-command` endpoint in FastAPI backend.
- [ ] Add audio recording & preset voice note clips in `CommandBar.tsx`.
- [ ] Automated tests covering voice command and high-impact verification.

### Sprint 2: Submission Deliverables (Rulebook Page 11)
- [ ] Author `docs/ACCOUNTABILITY_SHEET.md` (exact 4-quadrant matrix).
- [ ] Build `/audit/accountability` page in Next.js UI to showcase the sheet natively to judges.
- [ ] Author `docs/TEST_RESULTS_REPORT.md` linking all 20 test cases with Playwright screenshots.
- [ ] Validate blurb (under 10 words): *"Autonomous, accountable workplace agent for interview scheduling and reviews."* (9 words).

### Sprint 3: Judge Demo Day Sandbox
- [ ] Add "Judge Surprise Test Sandbox" tab with live 90s stopwatch and step-by-step telemetry.
- [ ] Rehearse 5–8 minute presentation flow with video recording guidelines.

---

## 5. Definition of Done for Final Submission

1. **Rulebook Compliance**: 100% of items in Rulebook Section 4 (Challenge B) and Section 7 (Submission Requirements) are met.
2. **Bonus Coverage**: All 4 bonus points implemented (Secondary Validator, High-Impact confirmation, Voice notes in Indonesian, 60s Undo window).
3. **Zero Critical Failures**: Confirmed 0 leaks, 0 unapproved dispatches, 0 prompt injection breaches.
4. **Automated Verification**: Full pytest test suite passing (> 60 tests), frontend typecheck and linting clean (0 errors), Playwright E2E browser tests documented.
5. **Ready for Demo Day**: Rehearsed live demonstration capable of resolving any surprise scenario in under 15 seconds (well within the 90s judge limit).
