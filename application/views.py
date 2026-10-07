import json
import subprocess
import sys
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Prediction
from .ml import DATA_DIR, MODEL_DIR, STATUS_FILE, artifacts_ready, load_dataset, predict_url

def home(request):
    metrics = {}
    path = MODEL_DIR / "metrics.json"
    if path.exists():
        metrics = json.loads(path.read_text())
    status = {}
    if STATUS_FILE.exists():
        try:
            status = json.loads(STATUS_FILE.read_text())
        except json.JSONDecodeError:
            status = {"status": "unknown", "message": "Training status unavailable."}
    return render(request, "home.html", {
        "metrics": metrics,
        "ready": artifacts_ready(),
        "training": status,
    })

def upload_dataset(request):
    if request.method != "POST":
        return redirect("home")
    f = request.FILES.get("dataset")
    if not f:
        messages.error(request, "Choose a CSV file.")
        return redirect("home")
    if not f.name.lower().endswith(".csv"):
        messages.error(request, "Only CSV files are supported.")
        return redirect("home")
    target = DATA_DIR / "malicious_phish.csv"
    with target.open("wb") as out:
        for chunk in f.chunks():
            out.write(chunk)
    try:
        df = load_dataset(target)
        messages.success(request, f"Dataset uploaded: {len(df):,} usable rows.")
    except Exception as exc:
        target.unlink(missing_ok=True)
        messages.error(request, str(exc))
    return redirect("home")

def train_models_view(request):
    if request.method != "POST":
        return redirect("home")
    dataset = DATA_DIR / "malicious_phish.csv"
    if not dataset.exists():
        messages.error(request, "Upload malicious_phish.csv first.")
        return redirect("home")
    status = {}
    if STATUS_FILE.exists():
        try:
            status = json.loads(STATUS_FILE.read_text())
        except json.JSONDecodeError:
            pass
    if status.get("status") in {"starting", "running"}:
        messages.info(request, "Training is already running.")
        return redirect("home")
    try:
        epochs = max(1, min(int(request.POST.get("epochs", "5")), 30))
    except ValueError:
        epochs = 5
    STATUS_FILE.write_text(json.dumps({
        "status": "starting",
        "message": "Training job is starting in the background...",
        "epoch": 0,
        "total_epochs": epochs,
    }, indent=2))
    log = (MODEL_DIR / "training.log").open("a", buffering=1)
    process = subprocess.Popen(
        [sys.executable, "manage.py", "train_models", "--dataset", str(dataset), "--epochs", str(epochs)],
        stdout=log,
        stderr=log,
        start_new_session=True,
        close_fds=True,
    )
    messages.success(request, f"Training started in background. Job ID: {process.pid}.")
    return redirect("home")

def predict_view(request):
    if request.method != "POST":
        return render(request, "predict.html", {"ready": artifacts_ready()})
    url = request.POST.get("url", "").strip()
    if not url:
        return render(request, "predict.html", {"ready": artifacts_ready(), "error": "Enter a URL."})
    try:
        label, confidence = predict_url(url, "hybrid")
        Prediction.objects.create(url=url, predicted_label=label, confidence=confidence)
        return render(request, "predict.html", {"ready": True, "url": url, "label": label, "confidence": f"{confidence*100:.2f}%"})
    except Exception as exc:
        return render(request, "predict.html", {"ready": artifacts_ready(), "error": str(exc)})

def evaluation_view(request):
    path = MODEL_DIR / "metrics.json"
    metrics = json.loads(path.read_text()) if path.exists() else {}
    return render(request, "evaluation.html", {"metrics": metrics})
