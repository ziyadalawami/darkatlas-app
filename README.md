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
└── /reports/
    └── GET  /generate         # Task 4: AI Executive Markdown Report
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

**1. Setup your `.env` file:**
Ensure your `.env` file is created and populated with your database credentials and OpenRouter API key as shown above.

**2. Build and run all containers:**

```bash
$ docker compose up --build
```

This will spin up both the PostgreSQL database and the FastAPI application inside isolated containers.

