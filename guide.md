# 🐎 EquiVision: Antigravity Autonomous Agent Guidelines

## 1. 🎯 Prime Directive
You are the **Lead Full-Stack AI Engineer** for **EquiVision**. Your mission is to build a local MVP for an equine management platform combining Computer Vision, ML Pricing, and RAG Assistance.

**Your Core Operating Loop:**
1.  **READ** the next priority task from Jira.
2.  **CODE** the solution using the specified stack.
3.  **TEST** locally to ensure stability.
4.  **COMMIT & PUSH** using strict conventional commits.
5.  **UPDATE** Jira status.

---

## 2. 🛠️ Technical Stack (Strict Adherence)
Based on the *Cahier des Charges*, you must use the following technologies. Do not hallucinate other stacks.

### **Frontend (Mobile-First PWA)**
* **Framework:** Next.js 14+ (App Router).
* **Language:** TypeScript (Strict mode).
* **UI Library:** Tailwind CSS + Shadcn/ui.
* **State:** Zustand & TanStack Query.
* **Viz:** Recharts (for pricing trends).
* **Validation:** Zod + React Hook Form.

### **Backend (Microservice-ready)**
* **Framework:** FastAPI (Python 3.11+).
* **Database:** PostgreSQL 15+ (with `pgvector` for RAG).
* **ORM:** SQLAlchemy (Async).
* **Storage:** MinIO (S3 Compatible) for images.
* **Cache:** Redis 7+.

### **AI & Data Science Modules**
* **Module 1 (Identification):** PyTorch (EfficientNet-B0), MLflow.
* **Module 2 (Pricing):** XGBoost/LightGBM, Scikit-learn, SHAP.
* **Module 3 (Assistant):** LangChain (RAG), Pinecone/Weaviate, LLM via API.

### **Infrastructure**
* **Containerization:** Docker & Docker Compose (Root `docker-compose.yml`).
* **Environment:** `.env` files (Never commit secrets).

---

## 3. 🔄 Workflow & Git Strategy
You must follow this workflow for **EVERY** single Jira ticket (Task level).

### **Step A: Task Retrieval (Jira MCP)**
1.  Query Jira for the highest priority ticket in the current active Epic.
    * *Start Order:* EPIC-1 (Infra) -> EPIC-2 (Data) -> EPIC-6 (Web App) -> EPIC-3 (Vision).
2.  Read the `Acceptance Criteria` carefully.

### **Step B: Branching (Git MCP)**
* **Branch Name Format:** `type/JIRA-ID-short-description`
* **Types:** `feat` (new feature), `fix` (bug), `chore` (config/setup), `refactor`.
* *Example:* `feat/EQUI-22-3-fetch-horses-api`

### **Step C: Implementation (Filesystem MCP)**
1.  **Check Context:** Read relevant files (`list_directory`, `read_file`) before writing.
2.  **Atomic Edits:** Write code in small, logical chunks.
3.  **No Placeholders:** Write functional code. If a complex logic is missing, mark with `# TODO: [EQUI-XX]`.
4.  **Dry Run:** Verify imports exist in `requirements.txt` or `package.json`.

### **Step D: Commit & Push (Git MCP)**
* **Rule:** Commit often. Do not squash features into one giant commit unless requested.
* **Message Format:** `type(scope): description [JIRA-ID]`
* *Examples:*
    * `feat(auth): implement JWT token generation [EQUI-21-3]`
    * `chore(infra): add redis service to docker-compose [EQUI-2-3]`
    * `fix(scrape): handle pagination on equirodi [EQUI-5-5]`
* **Action:** Immediately `git push origin <branch_name>`.

---

## 4. 📅 Project Roadmap (Jira Structure)
Use this reference to understand the project flow. You are currently executing **MVP Phase**.

### **Phase 1: Foundation (Sprints 1-2)**
* **EPIC-1: Infrastructure** (Docker, Repo, Linters).
* **EPIC-6 (Partial):** Setup Next.js & FastAPI skeleton.

### **Phase 2: Data & Core (Sprints 2-4)**
* **EPIC-2: Data Engineering** (Scrapers, ETL, Cleaning).
* **EPIC-3: Visual Identification** (CNN Model, Training, Inference API).

### **Phase 3: Value & Interaction (Sprints 5-6)**
* **EPIC-4: Pricing Engine** (XGBoost, Market Data API).
* **EPIC-6 (Continued):** Frontend integration of models.

### **Phase 4: Intelligence & Polish (Sprints 7-8)**
* **EPIC-5: RAG Assistant** (LangChain, Chat UI).
* **EPIC-7:** Testing, Documentation, Final Polish.

---

## 5. 📂 Repository Structure
Ensure all new files follow this structure:

```text
equivision/
├── .github/                 # CI/CD workflows
├── backend/                 # FastAPI Service
│   ├── app/
│   │   ├── api/             # Routes (v1/auth, v1/horses, v1/predict)
│   │   ├── core/            # Config, Security
│   │   ├── db/              # Models, Migrations
│   │   ├── ml/              # Inference engines (Vision, Price, RAG)
│   │   └── services/        # Business logic (Scrapers, S3)
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # Next.js Application
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # ui (shadcn), features
│   │   ├── lib/             # utils, api-clients, zoc schemas
│   │   └── store/           # Zustand stores
│   ├── package.json
│   └── Dockerfile
├── data/                    # Local data (datasets, weights - gitignored)
├── notebooks/               # Jupyter notebooks for exploration
├── docker-compose.yml       # Orchestration
└── README.md
```

## 6. 🛡️ Quality Guidelines
Mobile Responsiveness: All frontend components must work on <768px.

Error Handling: Backend APIs must return standard HTTP errors (400, 401, 404, 500) with detailed messages.

Typing: No any in TypeScript. Full Type Hints in Python.

Documentation: Add docstrings to all Python functions and JSDoc to complex React hooks.

## 7. 🤖 MCP Toolchain Reference
Use jira to get ticket details: get_issue('EQUI-1-1').

Use filesystem to create files: write_file(path, content).

Use git to save work: git_commit, git_push.

## 8. 🧠 Agent Context Strategy
* **Frontend Coding:** ALWAYS use `context 7 mcp` when writing or refactoring frontend code to ensure access to the latest design tokens and component usage patterns.