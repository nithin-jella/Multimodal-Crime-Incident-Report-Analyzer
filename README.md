# Multimodal Crime / Incident Report Analyzer

This project runs Python pipelines on **audio**, **images**, **video**, **text**, and **documents (PDF/DOCX)**, then merges results into CSV files. A **React dashboard** in `dashboard/` shows all incidents in one searchable table.

**Repository:** [AdithyaReddyGeeda/Multimodal-Crime-Incident-Report-Analyzer](https://github.com/AdithyaReddyGeeda/Multimodal-Crime-Incident-Report-Analyzer)

---

## Read this first

1. **Always use the project root** — the folder that contains `main.py`, `modules/`, and `dashboard/`. If you run Python from inside `dashboard/`, paths will break.
2. **Use a Python virtual environment** so dependencies do not clash with other projects.
3. **After** the pipelines finish, run **`sync_dashboard_data.py`** once, then start the dashboard. The website reads data from `dashboard/src/data/*.js`, not directly from the CSV files.

---

## What you need installed

| Software | Why |
|----------|-----|
| **Python 3.9+** | Runs all analysis scripts |
| **Node.js (LTS)** | Runs the React dashboard (`npm run dev`) |

**Optional (some features work better with these):**

| Software | Why |
|----------|-----|
| **Tesseract** | OCR text inside images (`brew install tesseract` on Mac) |
| **FFmpeg** | Helpful for audio/video tooling on some systems |
| **Roboflow API key** | Cloud image model; without it, the image module may use a local YOLO fallback |

---

## Step-by-step: run the project from zero

### 1. Get the code and enter the folder

```bash
git clone https://github.com/AdithyaReddyGeeda/Multimodal-Crime-Incident-Report-Analyzer.git
cd Multimodal-Crime-Incident-Report-Analyzer
```

If you already have the folder, open a terminal and `cd` into it (the directory that contains `main.py`).

---

### 2. Create the Python environment and install packages

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m nltk.downloader stopwords punkt punkt_tab
```

**Windows (Command Prompt or PowerShell):**

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m nltk.downloader stopwords punkt punkt_tab
```

You should see `(.venv)` in your terminal prompt when the environment is active. **Run all `python` / `python3` commands below only after activating.**

---

### 3. Install dashboard dependencies (one time)

From the **project root** (not inside `dashboard/` yet):

```bash
cd dashboard
npm install
cd ..
```

---

### 4. API key for images (optional)

```bash
cp .env.example .env
```

Edit `.env` in the project root and set:

```env
ROBOFLOW_API_KEY=your_key_here
```

Get a key at [roboflow.com](https://roboflow.com). If you skip this, the image pipeline may still run using a local model, depending on your setup.

**Do not commit `.env`.** It is listed in `.gitignore`.

---

### 5. Put data where the scripts expect it

The pipelines read from fixed paths. If something is missing, that module may print a warning or produce an empty CSV.

| Module | What it needs | Typical location |
|--------|----------------|------------------|
| **Audio** | Transcript CSV | `data/audio/transcripts.csv` |
| **Image** | Test images | `fire-detection.v1i.yolov8/test/images/` (YOLO dataset layout) |
| **Video** | Video files | `data/videos/` (e.g. `.mpg`, `.mp4`) |
| **Text** | Crime-style text | `data/text/` or `data/Text/` — e.g. `CrimeReport.txt` or CSV (see `modules/text_analyst.py` for supported names) |
| **Document** | PDF / DOCX / TXT | `data/documents/` |

The repo may already include some of this (for example audio and text). **Large** items (full image dataset, CAVIAR videos, external PDFs) are often **not** in Git — download them separately if your assignment requires them. See **“Downloading datasets”** at the end of this file for links.

---

### 6. Run the full pipeline

Stay in the **project root**. Activate `.venv` if needed, then:

```bash
python3 main.py
```

On Windows, if `python3` is not found, use `python main.py`.

`main.py` runs these steps **in this order** (each step is wrapped in `try`/`except` so a failure in one step does not stop the rest):

1. Audio analyst  
2. Image analyst  
3. Video analyst  
4. Text analyst  
5. Document analyst  
6. Integrator (merges all module CSVs into `outputs/final_integrated_report.csv`)

The first run can take a long time while models download.

---

### 7. Copy results into the dashboard, then open the website

Still from the **project root**:

```bash
python3 sync_dashboard_data.py
cd dashboard
npm run dev
```

Your terminal will show a local URL — open it in a browser (often **http://localhost:5173**).

Whenever you regenerate CSVs in `outputs/`, run **`python3 sync_dashboard_data.py`** again before refreshing the app.

---

## Run one module at a time (optional)

Use the same project root and active venv. Order matches `main.py`:

```bash
python3 modules/audio_analyst.py
python3 modules/image_analyst.py
python3 modules/video_analyst.py
python3 modules/text_analyst.py
python3 modules/document_analyst.py
python3 modules/integrator.py
```

---

## Outputs

After running the pipelines, look in **`outputs/`**:

| File | Meaning |
|------|---------|
| `audio_output.csv` | Audio module |
| `image_output.csv` | Image module |
| `video_output.csv` | Video module |
| `text_output.csv` | Text module |
| `document_output.csv` | Document module |
| `final_integrated_report.csv` | Integrator (all sources combined) |

---

## Project layout (short)

```
main.py                 # Full pipeline entry point
sync_dashboard_data.py # CSV → dashboard/src/data/*.js
requirements.txt
.env                    # Create locally; never commit

modules/                # audio_analyst, image_analyst, video_analyst,
                        # text_analyst, document_analyst, integrator

data/                   # audio, videos, text, documents, etc.
outputs/                # Generated CSVs (created when you run pipelines)

dashboard/              # React app — npm install once, then npm run dev
```

**Extra files (if present):** `dashboard/pipeline_architecture.html` (open in a browser for a diagram), `project_report.docx` (written report).

---

## Common problems

| Problem | What to do |
|---------|------------|
| `No such file ... modules/...` or `can't open file 'modules/...'` | You are not in the project root. `cd` to the folder that contains `main.py`, then run the command again. |
| `No module named 'pandas'` (or similar) | Activate `.venv` and run `pip install -r requirements.txt` again. |
| Dashboard is empty or old | Run `python3 sync_dashboard_data.py` from the project root after generating CSVs. |
| Image step fails | Check `ROBOFLOW_API_KEY` in `.env` and that image paths match `modules/image_analyst.py`. |
| Video step fails | Put video files under `data/videos/` and check formats your script supports. |
| Document step produces no rows | Add at least one `.pdf`, `.docx`, or `.txt` under `data/documents/`. |

---

## Downloading datasets (when not bundled in the repo)

These are **examples** — follow your course or assignment instructions for required files.

- **Fire detection images:** [Roboflow Fire Detection](https://universe.roboflow.com/) — download YOLOv8 format and extract so `fire-detection.v1i.yolov8/test/images/` exists under the project root.  
- **CAVIAR CCTV:** [CAVIAR dataset](https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA1/) — place `.mpg` (or supported) files in `data/videos/`.  
- **Sample PDF for documents:** add any police-report-style PDF to `data/documents/` or use sources linked in your assignment.

---

## License and data

Third-party datasets and APIs have their own terms. Do not commit API keys, passwords, or private data.
