# DarkAtlas Asset Management API
An Asset Management API built with FastAPI, PostgreSQL, and LangChain to ingest, deduplicate, and analyze external attack surface assets.

## 🚀 API Endpoint Map

```text
/api/v1
├── /assets/
│   ├── POST /                 # Ingest a single asset
│   ├── POST /batch            # Batch ingest arrays & map relationships
│   ├── POST /query            # Task 1: Natural Language AI Query
│   ├── GET  /{id}/analyze     # Task 2: AI Vulnerability Analysis
│   └── POST /{id}/categorize  # Task 3: AI Categorization & Tagging
├── /reports/
│   └── GET  /generate         # Task 4: AI Executive Markdown Report
└── /agent/
    └── POST /chat             # Bonus Task: Autonomous Security Agent
```

---

## 🛠️ Requirements

* Python 3.11
* Docker Desktop installed and running
* Miniconda (recommended for local development)

---

## 💻 Local Development Setup (Recommended for coding)

Use this method if you are actively writing code and want the FastAPI server to hot-reload when you save files.

**1. Create a new environment using Miniconda:**

```bash
$ conda create -n darkatlas-app python=3.11 -y
```

**2. Activate the environment:**

```bash
$ conda activate darkatlas-app
```

**3. Install the required packages:**

```bash
$ pip install -r requirements.txt
```

**4. Setup the environment variables:**

```bash
$ cp .env.example .env
```

**5. Configure your `.env` file:** Open the `.env` file and configure these exact values:

```env
DB_USER=admin
DB_PASSWORD=your_local_database_password            # <- set a password to your database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=asset_management
OPENROUTER_API_KEY=your_openrouter_api_key_here     # <- set your OpenRouter API key
```

**6. Run the Database Container:**
*Note: This starts only the PostgreSQL database.*

```bash
$ docker compose up -d db
```

**7. Run the Host API:**

```bash
$ uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. You can view the interactive Swagger documentation at `http://localhost:8000/docs`.

---

## 🐳 Docker Deployment

Use this method if you just want to run the application fully containerized without setting up a local Python environment.

**1. Setup the environment variables:**

```bash
$ cp .env.example .env
```

*(Remember to add your database credentials and OpenRouter API key to the `.env` file!)*

**2. Build and start all services (API + Database):**

```bash
$ docker compose up --build
```

The API will be available at `http://localhost:8000/docs`.

---

## 💡 Usage Examples

You can test all API functionalities using the interactive Swagger UI at `http://localhost:8000/docs`, or via a tool like Postman. Be sure to replace `{id}` in the path parameters with a valid PostgreSQL UUID from your database.

### 1. Ingest a Single Asset

**POST** `/api/v1/assets/`

```json
{
  "type": "domain",
  "value": "darkatlas.io",
  "source": "manual_entry",
  "status": "active",
  "tags": ["corporate-root"],
  "metadata": {
    "registrar": "Cloudflare"
  }
}
```

### 2. Batch Ingest & Map Relationships

Demonstrates the two-pass batch system mapping temporary JSON IDs to database UUIDs.
**POST** `/api/v1/assets/batch`

```json
[
  {
    "id": "a1",
    "type": "domain",
    "value": "example.com",
    "source": "scan",
    "tags": ["root"]
  },
  {
    "id": "a2",
    "type": "subdomain",
    "value": "api.example.com",
    "source": "scan",
    "parent": "a1"
  }
]
```

### 3. Natural Language Asset Query (Task 1)

Translate English into structured database filters to find specific assets.
**POST** `/api/v1/assets/query`

```json
{
  "query": "Find all highly critical staging databases"
}
```

### 4. AI Vulnerability Analysis (Task 2)

Generate a high-impact security assessment for a specific asset.
**GET** `/api/v1/assets/{id}/analyze`
*(No payload required. Pass the asset's UUID in the URL path.)*

### 5. Automated AI Categorization (Task 3)

Instructs the LLM to classify an asset's environment, category, and criticality, then saves it to the DB.
**POST** `/api/v1/assets/{id}/categorize`
*(No payload required. Pass the asset's UUID in the URL path.)*

### 6. AI Executive Markdown Report (Task 4)

Generate a comprehensive security brief summarizing the entire external attack surface.
**GET** `/api/v1/reports/generate`
*(No payload required. Returns a formatted markdown report.)*

### 7. Autonomous Security Agent (Bonus Task)

Ask a complex security question. The LangChain agent will autonomously call internal API tools to fetch the required data before responding.
**POST** `/api/v1/agent/chat`

```json
{
  "question": "Query the database for 'prod' environment assets. Tell me how many there are and give me a brief security summary of them."
}
```
