# GeneLens AI

GeneLens AI is a privacy-first clinical blood-sample analysis platform. It separates real patient identity information from clinical records by assigning anonymous patient IDs, then provides laboratory summaries, risk signals, recommendations, history, and audit information.

> **Important:** GeneLens AI is a software project for research and demonstration. Its results are not a medical diagnosis and must not replace professional clinical judgment.

## Features

- Streamlit dashboard for registering patients and reviewing anonymous clinical records
- Anonymous patient ID generation and identity-vault separation
- Blood-sample record storage and normalization
- Rule-based risk scoring with signals and recommendations
- CSV upload support for blood-sample data
- Patient history and investigation summaries
- User registration, login, role checks, and access logging
- FastAPI endpoints for application integrations
- Docker and Render deployment configuration

## Project Structure

```text
.
├── app.py                 # Streamlit user interface
├── api.py                 # FastAPI application and routes
├── backend.py             # Clinical storage, scoring, roles, and audit logic
├── dna.py                # DNA-related project utilities
├── gene_data_loader.py    # Gene data loading helpers
├── preprocess.py          # Data preprocessing utilities
├── clinical_data.db       # Local SQLite data store
├── gene_model.pkl         # Serialized model artifact
├── tests/                 # Unit tests
├── Dockerfile             # Container configuration
├── render.yaml            # Render deployment configuration
└── requirements.txt       # Python dependencies
```

## Requirements

- Python 3.12 or later recommended
- `pip`
- Optional: Docker

## Local Setup

Create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the Streamlit dashboard:

```powershell
streamlit run app.py
```

Open the local URL shown by Streamlit, normally `http://localhost:8501`.

## FastAPI Service

Start the API in development mode:

```powershell
uvicorn api:app --reload
```

The API is then available at `http://127.0.0.1:8000`.

Interactive API documentation is available at:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

### Main API Routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check service health |
| `POST` | `/identity/register` | Register an identity and generate an anonymous patient ID |
| `POST` | `/auth/register` | Create a user with a role |
| `POST` | `/auth/login` | Authenticate a user |
| `POST` | `/clinical-record` | Store a clinical record |
| `GET` | `/patients/{patient_id}` | Retrieve an anonymous patient summary |
| `GET` | `/patients/{patient_id}/history` | Retrieve patient record history |
| `GET` | `/patients/{patient_id}/investigate` | Generate an investigation summary |
| `GET` | `/audit` | View recent audit entries |

Patient summary, history, and investigation routes enforce doctor, admin, or auditor access roles.

## CSV Upload Format

CSV files should include the laboratory fields needed by the dashboard. The parser accepts either lowercase field names or the display-style names used by the interface.

```csv
patient_id,sample_id,blood_group,hemoglobin,wbc,platelets,glucose,sodium,potassium,hydration_score,nutrition_flag,doctor_note
P-1001,S-01,A+,13.2,8.1,240,96,140,4.1,72,normal,Routine follow-up
```

## Testing

Run the test suite from the project root:

```powershell
python -m pytest -q
```

## Docker

Build and run the Streamlit application with Docker:

```powershell
docker build -t genelen-ai .
docker run --rm -p 8501:8501 genelen-ai
```

Open `http://localhost:8501` after the container starts.

## Deployment with Render

The included `render.yaml` configures a Python web service that installs `requirements.txt` and starts Streamlit on Render's assigned port. Connect the GitHub repository to Render and use the existing Blueprint configuration.

## Privacy and Security Notes

- Do not commit real patient names, credentials, API keys, or production clinical data.
- Keep Streamlit secrets in `.streamlit/secrets.toml`; this file is ignored by Git.
- Review `clinical_data.db` before publishing or deploying publicly.
- Use HTTPS, a managed database, proper secret management, and production authentication before handling real clinical information.
- Validate all risk signals and recommendations with qualified healthcare professionals.

## License

No license has been specified for this project yet.
