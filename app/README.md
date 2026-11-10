# A-Eye MVP

React + Vite frontend and FastAPI backend for the first Pokémon Card PreGrader workflow.

See the [application architecture diagram](../docs/architecture-diagram.svg) for components, data flows, Gemini disclosure, and secret handling. The editable Mermaid source is [architecture-diagram.mmd](../docs/architecture-diagram.mmd).

## Run with Docker Compose

From `app/`:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). The API key is optional; centering and photo-quality checks work without it. Add `GEMINI_API_KEY` to `.env` to enable optional condition observations. The app asks before sending the photo to Gemini.

For frontend development with Docker hot reload, run from `app/`:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Open [http://localhost:5173](http://localhost:5173). The dev service bind-mounts `frontend/`; Vite watches mounted files with polling and pushes updates to the browser. Stop it with the same two compose files and `down`. Change the browser port with `DEV_APP_PORT` in `.env`.

## Run locally without Docker

Start the backend from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r app\backend\requirements.txt
uvicorn app.backend.main.app:app --reload
```

In another terminal:

```powershell
cd app\frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). To use Gemini, set `GEMINI_API_KEY` in the environment before starting the backend.

## MVP scope and limitations

- Uploads JPEG, PNG, or WebP (10 MB default), performs basic image size, exposure, and focus checks, and gives retake guidance.
- Photo input supports selecting an existing image or opening a live camera preview to take a picture. Camera access requires browser permission and HTTPS or localhost.
- The user marks the four outside card corners and four inner printed-border corners. The app rectifies perspective and estimates opposing border ratios; accuracy depends on manually selected landmarks.
- Optional Gemini image analysis reports possible visible condition issues. It is not run unless selected and confirmed; the photo is sent to the configured provider and is not stored by this app.
- The app backend contains its own Gemini prompt, defect categories, response schema, and centering implementation. The experiment is a separate project and is not included in the app's Docker build context or runtime.
- If Gemini rejects an analysis request, the error popup includes its response body (limited to 4,000 bytes, with the API key redacted) to help diagnose the problem.
- The report explains the photo-quality check, card outline, centering estimate, and whether condition observations were performed.
- The MVP does not assign a numerical grade: it has no calibrated grading model or validated thresholds. Model-reported confidence is not calibrated; photos can miss defects, and centering depends on manual landmarks.

The app does not authenticate cards or provide an official grade or financial guarantee.
