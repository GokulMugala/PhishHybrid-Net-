# Phishing Detection — Working Django + Hybrid Bi-LSTM/Bi-GRU

This repository contains a cleaned, runnable version of the phishing-detection project.

## Included

- Django web application
- CSV dataset upload and validation
- Four-class URL classification: benign, defacement, malware, phishing
- Character-level URL tokenizer
- Bi-LSTM model
- Bi-GRU model
- Hybrid Bi-LSTM + Bi-GRU model
- Accuracy, precision, recall and F1 evaluation
- Single-URL prediction
- Saved model artifacts under `model/`
- SQLite prediction history
- No request-global ML training state

## Dataset

The expected full dataset is `malicious_phish.csv` with:

```text
url,type
```

Place the full dataset at:

```text
data/malicious_phish.csv
```

A small sample is included as `data/malicious_phish_sample.csv` only to verify the workflow. It is not suitable for meaningful model evaluation.

## Setup

### Windows

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Train

Upload the full CSV from the home page, or copy it to `data/malicious_phish.csv`, then run:

```bash
python manage.py train_models --dataset data/malicious_phish.csv --epochs 5
```

Training can take a while, especially on CPU.

## Project structure

```text
PhishHybrid-Net-/
├── Phising_detection/       # Django project configuration
├── application/             # Django app + ML pipeline
├── templates/               # Web UI
├── data/                    # Dataset location
├── manage.py
└── requirements.txt
```

The original source had Django modules at the repository root while `manage.py` expected a `Phising_detection` package and the URL configuration expected an `application` package. This version uses a consistent Django package structure and persists model artifacts to disk so separate HTTP requests work correctly.
