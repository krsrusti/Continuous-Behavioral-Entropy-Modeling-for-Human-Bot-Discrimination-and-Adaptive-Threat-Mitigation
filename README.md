# TIF Bot / LLM Detection Project

This project builds a browser-based behavioral trap system to collect interaction telemetry and classify sessions as human, bot, or LLM-generated traffic using a machine learning pipeline.

It combines:

- a trap-style web interface that captures passive user behavior and micro-probe interactions
- a Flask backend that stores session data and scores risk
- feature extraction for mouse, typing, scrolling, and response timing patterns
- a trained Random Forest classifier for session classification

The system is organized into four rooms/modules:

- `room1_trap_page` — browser pages and trap UI
- `room2_backend` — Flask API, session storage, and risk endpoints
- `room3_features` — feature extraction logic
- `room4_classifier` — model training, evaluation, and saved model artifacts

## Project goal

The goal is to detect automated or synthetic traffic by measuring subtle behavior differences in:

- reaction times to browser probes
- cursor movement and hesitation patterns
- typing rhythm and click timing
- scrolling and interaction burstiness
- session-level behavioral fingerprints

This is intended as a research and prototyping project for behavior-based bot and LLM detection.

## Architecture

```text
room1_trap_page/        Browser UI + passive telemetry capture
  ├─ templates/
  ├─ static/js/
  └─ static/css/

room2_backend/          Flask API + database + risk scoring endpoints
  ├─ api/
  ├─ database/
  ├─ models/
  └─ app.py

room3_features/         Feature extraction pipeline
  ├─ extractors/
  ├─ calculators/
  └─ pipeline.py

room4_classifier/       Model training and evaluation
  ├─ train.py
  ├─ evaluate.py
  └─ saved_models/

data/                  Session datasets and SQLite database
scripts/                Data generation and automation utilities
```

## Key capabilities

- Collect passive browser events such as mouse movement, typing, scrolling, and clicks
- Inject lightweight behavioral probes during user interaction
- Save session data to SQLite via Flask endpoints
- Extract 12 behavioral features used by the ML model
- Train and evaluate a Random Forest classifier
- Return a risk band, probability breakdown, and action label for a session

## Tech stack

- Python 3
- Flask
- SQLAlchemy
- SQLite
- NumPy / Pandas / SciPy
- scikit-learn
- JavaScript (browser collection scripts)

## Repository structure

```text
.
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── reference.txt
├── check_probe_performance.py
├── data/
│   ├── tif.db
│   └── sessions/
├── room1_trap_page/
│   ├── static/
│   └── templates/
├── room2_backend/
│   ├── api/
│   ├── database/
│   ├── models/
│   └── app.py
├── room3_features/
│   ├── calculators/
│   ├── extractors/
│   └── pipeline.py
├── room4_classifier/
│   ├── evaluate.py
│   ├── feature_diagnostic.py
│   ├── predict.py
│   ├── probe_diagnostic.py
│   ├── train.py
│   └── saved_models/
├── scripts/
│   ├── bot_mid_session_attack.py
│   ├── collect_dataset.py
│   ├── export_sessions.py
│   ├── generate_synthetic_sessions.py
│   └── ...
└── requirements.txt
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file at the project root if needed and provide values such as:

```env
SECRET_KEY=your-secret-key
RECAPTCHA_SECRET_KEY=your-recaptcha-secret
```

The backend reads these values in `room2_backend/app.py`.

## Run the project

### Start the backend

```bash
python room2_backend/app.py
```

The Flask API will run on:

- `http://localhost:5000`

Health check:

```bash
http://localhost:5000/api/health
```

### Start the trap page frontend

Serve the browser UI from `room1_trap_page`:

```bash
cd room1_trap_page
python -m http.server 8080
```

Then open:

```text
http://localhost:8080/templates/login.html
```

This page collects interaction data and sends it to the backend for risk scoring.

## Train the classifier

Run the model training script:

```bash
python room4_classifier/train.py
```

This trains the Random Forest model and saves it to:

```text
room4_classifier/saved_models/rf_model.pkl
```

## Example risk API call

```bash
curl -X POST http://localhost:5000/api/risk \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_session_001",
    "passive_events": [],
    "probes": []
  }'
```

The response includes:

- `score`
- `band`
- `action`
- `label`
- `prediction`
- `probabilities`

## Data and experimentation

The project includes:

- synthetic/generated session data in `data/sessions/`
- SQLite database storage under `data/tif.db`
- scripts for session generation, export, and attack simulation

Useful scripts include:

- `scripts/generate_synthetic_sessions.py`
- `scripts/collect_dataset.py`
- `scripts/export_sessions.py`
- `scripts/bot_mid_session_attack.py`
- `scripts/playtest.py`

## Notes

This project is designed as a research prototype and is not a production-grade security or fraud system by itself. It demonstrates how behavioral telemetry and lightweight probes can be used to profile suspicious sessions and estimate whether traffic is human, bot, or synthetic/LLM-driven.

## License

This project does not appear to include a formal license file. If you plan to publish this repository publicly, consider adding an open-source license such as MIT or Apache 2.0.

## Contributing

Contributions are welcome for:

- improving feature extraction quality
- better model evaluation and robustness
- cleaner API contracts
- stronger dataset tooling and experiment tracking

## Acknowledgements

This project uses behavioral fingerprinting and session analysis ideas for anti-bot and browser risk detection research. It is intended for learning, experimentation, and applied security research use cases.
