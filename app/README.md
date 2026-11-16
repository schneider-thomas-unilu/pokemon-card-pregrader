# A-Eye MVP

React + Vite frontend and FastAPI backend for the first Pokémon Card PreGrader workflow.

See the [application architecture diagram](../docs/architecture-diagram.svg) for components, data flows, Gemini disclosure, and secret handling. The editable Mermaid source is [architecture-diagram.mmd](../docs/architecture-diagram.mmd).

## Requirements

For the recommended Docker setup:

- Windows 10 or 11
- Docker Desktop
- Windows Subsystem for Linux (WSL 2)
- An internet connection for downloading dependencies and building containers

Python and Node.js do not need to be installed separately when using Docker.

## Quick Start: Run with Docker

### 1. Download the project

- Open the project's GitHub repository.
- Select **Code → Download ZIP**.
- Extract the downloaded ZIP file to your computer.

### 2. Install Docker Desktop

- Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
- If prompted, enable the **Virtual Machine Platform** and **Windows Subsystem for Linux** Windows features:
  1. Press `Windows + R`.
  2. Enter `optionalfeatures` and press Enter.
  3. Enable both features.
  4. Click OK and restart your computer if requested.
- If WSL 2 is not installed, open PowerShell as Administrator and run:

  ```powershell
  wsl --install
  wsl --update
  ```

- Open Docker Desktop and wait until Docker is running.

### 3. Configure the application

- Open the extracted project folder.
- Open the `app` directory in PowerShell.
- Create the environment file:

  ```powershell
  Copy-Item .env.example .env
  ```

- To enable Gemini-powered condition observations, open `app/.env` and add your Gemini API key:

  ```env
  GEMINI_API_KEY=your_api_key_here
  ```

- The API key is optional. Photo-quality checks and centering analysis work without it.

**Important:** Do not commit your `.env` file or share your API key.

### 4. Build and start the application

From inside the `app` directory, run:

```powershell
docker compose up --build
```

Docker builds and starts the frontend and backend. The first build may take several minutes.

### 5. Open the application

Open your browser and visit:

**http://localhost:8080**

To stop the application, press `Ctrl+C` in the terminal and run:

```powershell
docker compose down
```

## Gemini configuration

The application uses Google's Gemini API for optional visible-condition observations.

- The configured default model is `gemini-3.8-flash`.
- The model can be changed through the `GEMINI_MODEL` environment variable in `app/.env`.
- Alternative models, including Gemini 3.5 and 3.1, have also been used for testing.
- Gemini availability and API quotas may affect whether an analysis request succeeds.
- The application asks for user confirmation before sending a card photo to Gemini.
- Photos sent for analysis are not stored by this application.

Without a Gemini API key, users can still perform photo-quality checks and centering analysis.

## Development setup

### Docker development mode

For frontend development with Vite hot reload, run the following from `app/`:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Open:

**http://localhost:5173**

The development service bind-mounts `frontend/`. Vite watches mounted files and updates the browser when changes are made.

To stop the development environment:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

The browser port can be changed using `DEV_APP_PORT` in `app/.env`.

### Run locally without Docker

Python and Node.js must be installed for this option.

Start the backend from the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r app\backend\requirements.txt
uvicorn app.backend.main.app:app --reload
```

In a second terminal, start the frontend:

```powershell
cd app\frontend
npm install
npm run dev
```

Open:

**http://localhost:5173**

To use Gemini, configure `GEMINI_API_KEY` in the environment before starting the backend.

## MVP scope and limitations

- Supports JPEG, PNG, and WebP uploads, with a default 10 MB upload limit.
- Performs basic image size, exposure, and focus checks and provides retake guidance.
- Supports selecting an existing image or using a live camera preview. Camera access requires browser permission and HTTPS or localhost.
- Users manually mark the four outside card corners and four inner printed-border corners.
- The application rectifies perspective and estimates opposing border ratios. Accuracy depends on the manually selected landmarks.
- Optional Gemini image analysis reports possible visible condition issues. It only runs after the user selects and confirms the analysis.
- The backend contains its own Gemini prompt, defect categories, response schema, and centering implementation. The separate experiment is not included in the app's Docker build context or runtime.
- If Gemini rejects an analysis request, the error popup includes a limited portion of the provider response to help diagnose the problem, with the API key redacted.
- The report presents photo quality, card outline, centering estimates, and whether condition observations were performed.
- The MVP does not assign a numerical grade because it does not have a calibrated grading model or validated grading thresholds.
- Model-reported confidence is not calibrated. Photo quality, lighting, viewing angle, and manual landmark selection can affect the results.

The application does not authenticate cards or provide an official grade or financial guarantee.

## Known Bugs and Limitations

1. **Imprecise manual corner placement:** Selecting the four outside card corners and four inner-border corners can be difficult. Inaccurate placement can affect centering measurements.

2. **Gemini 3.8 Flash availability:** The intended model is frequently overloaded or temporarily unavailable. This can delay or prevent AI analysis. An alternative supported model may be needed for testing.

3. **Photo-quality sensitivity:** Glare, blur, poor lighting, and viewing angle can affect defect observations. Users may need to retake photos to obtain useful results.

4. **Unvalidated AI observations:** Gemini may miss defects or identify defects that are not present. Confidence values are not calibrated probabilities, and the application does not provide an official grade.

5. **Single-photo limitations:** A front-facing photo cannot reveal every bend, crease, or defect, particularly on the reverse side or when damage is visible only from an angle.