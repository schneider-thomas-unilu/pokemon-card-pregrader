# A-Eye MVP

React + Vite frontend and FastAPI backend for the first Pokémon Card PreGrader workflow.

## Run with Docker Compose

From `app/`:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). The API key is optional; without one, centering and the user-input profit comparison still work. Add `GEMINI_API_KEY` to `.env` to enable optional vision observations. The app asks before sending the photo to Gemini.

For frontend development with Docker hot reload, run from `app/`:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Open [http://localhost:5173](http://localhost:5173). The dev service bind-mounts `frontend/`; Vite watches mounted files with polling and pushes updates to the browser. Stop it with the same two compose files and `down`. Change the browser port with `DEV_APP_PORT` in `.env`.

The `health-monitor` service polls `/health` every 20 seconds by default and prints timestamped pass/fail messages to stdout. `docker compose up` shows these alongside the API logs. To follow them later, run:

```powershell
docker compose logs -f backend health-monitor
```

Set `HEALTH_CHECK_INTERVAL_SECONDS` and `HEALTH_CHECK_TIMEOUT_SECONDS` in `.env` to change the polling cadence and timeout.

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

To run the same health monitor in a separate terminal from the repository root:

```powershell
python -m app.backend.main.health_monitor --url http://127.0.0.1:8000/health --interval 20
```

## MVP scope and limitations

- Uploads JPEG, PNG, or WebP (10 MB default), performs basic image size, exposure, and focus checks, and gives retake guidance.
- Photo input supports selecting an existing image or opening a device camera on supported phones and browsers.
- The user marks the four outer card corners and four inner-border corners. The backend uses the experiment's existing perspective-corrected centering implementation.
- Optional Gemini image analysis reports possible visible condition issues. It is not run unless selected and confirmed; the photo is sent to the configured provider and is not stored by this app.
- The raw-vs-grade-7/8 comparison uses the prices and costs entered by the user. It is an illustrative calculation, not a price feed or financial recommendation.
- The MVP does not predict a grade or estimate grade likelihood. Model-reported confidence is not calibrated; photos can miss defects, and centering depends on manual landmarks.

The app does not authenticate cards or provide an official grade or financial guarantee.
