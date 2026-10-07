from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Bidirectional, LSTM, GRU, Dense, Dropout
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model"
DATA_DIR = BASE_DIR / "data"
MODEL_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

MAX_LEN = 150
VOCAB_LIMIT = 12000
EMBED_DIM = 48
RNN_UNITS = 64
LABELS = ["benign", "defacement", "malware", "phishing"]

def load_dataset(path):
    df = pd.read_csv(path, low_memory=False)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "url" not in df.columns or "type" not in df.columns:
        raise ValueError("Dataset must contain 'url' and 'type' columns.")
    df = df[["url", "type"]].dropna()
    df["url"] = df["url"].astype(str).str.strip().str.lower()
    df["type"] = df["type"].astype(str).str.strip().str.lower()
    df = df[df["url"].ne("")]
    df = df[df["type"].isin(LABELS)]
    df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)
    if df["type"].nunique() < 2:
        raise ValueError("Dataset must contain at least two classes.")
    return df

def build_model(kind, vocab_size, num_classes):
    inputs = Input(shape=(MAX_LEN,))
    x = Embedding(vocab_size, EMBED_DIM)(inputs)
    if kind == "bilstm":
        x = Bidirectional(LSTM(RNN_UNITS))(x)
    elif kind == "bigru":
        x = Bidirectional(GRU(RNN_UNITS))(x)
    elif kind == "hybrid":
        x = Bidirectional(LSTM(RNN_UNITS, return_sequences=True))(x)
        x = Bidirectional(GRU(RNN_UNITS))(x)
    else:
        raise ValueError("Unknown model kind.")
    x = Dropout(0.30)(x)
    x = Dense(64, activation="relu")(x)
    x = Dropout(0.20)(x)
    outputs = Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model

def train_all(dataset_path, epochs=5, test_size=0.34):
    df = load_dataset(dataset_path)
    x_train, x_test, y_train, y_test = train_test_split(
        df["url"].values,
        df["type"].values,
        test_size=test_size,
        random_state=42,
        stratify=df["type"].values,
    )
    tokenizer = Tokenizer(num_words=VOCAB_LIMIT, char_level=True, oov_token="[OOV]")
    tokenizer.fit_on_texts(x_train)
    X_train = pad_sequences(tokenizer.texts_to_sequences(x_train), maxlen=MAX_LEN, padding="post", truncating="post")
    X_test = pad_sequences(tokenizer.texts_to_sequences(x_test), maxlen=MAX_LEN, padding="post", truncating="post")
    le = LabelEncoder()
    le.fit(df["type"])
    ytr = le.transform(y_train)
    yte = le.transform(y_test)
    joblib.dump(tokenizer, MODEL_DIR / "tokenizer.pkl")
    joblib.dump(le, MODEL_DIR / "label_encoder.pkl")
    results = {}
    for kind in ("bilstm", "bigru", "hybrid"):
        model = build_model(kind, min(VOCAB_LIMIT, len(tokenizer.word_index) + 1), len(le.classes_))
        callbacks = [tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=2, restore_best_weights=True)]
        model.fit(X_train, ytr, validation_split=0.1, epochs=epochs, batch_size=128, callbacks=callbacks, verbose=2)
        model.save(MODEL_DIR / f"{kind}.keras")
        probs = model.predict(X_test, batch_size=512, verbose=0)
        preds = np.argmax(probs, axis=1)
        p, r, f, _ = precision_recall_fscore_support(yte, preds, average="weighted", zero_division=0)
        results[kind] = {
            "accuracy": float(accuracy_score(yte, preds)),
            "precision": float(p),
            "recall": float(r),
            "f1": float(f),
            "confusion_matrix": confusion_matrix(yte, preds).tolist(),
        }
    (MODEL_DIR / "metrics.json").write_text(json.dumps(results, indent=2))
    return results

def artifacts_ready():
    return all((MODEL_DIR / f).exists() for f in ["tokenizer.pkl", "label_encoder.pkl", "hybrid.keras"])

def predict_url(url, model_kind="hybrid"):
    if not artifacts_ready():
        raise FileNotFoundError("Train the models first.")
    tokenizer = joblib.load(MODEL_DIR / "tokenizer.pkl")
    le = joblib.load(MODEL_DIR / "label_encoder.pkl")
    model = tf.keras.models.load_model(MODEL_DIR / f"{model_kind}.keras")
    seq = pad_sequences(tokenizer.texts_to_sequences([url.strip().lower()]), maxlen=MAX_LEN, padding="post", truncating="post")
    probs = model.predict(seq, verbose=0)[0]
    idx = int(np.argmax(probs))
    return str(le.inverse_transform([idx])[0]), float(probs[idx])
