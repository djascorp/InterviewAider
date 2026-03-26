# Interview Assistant — Fiche Projet Python

**Version :** 1.0  
**Date :** 25 mars 2026  
**Plateforme cible :** Windows 10 (build 2004+) / Windows 11  
**Durée estimée :** 3 à 5 jours

---

## 1. Description du projet

Application desktop Windows qui écoute en continu l'audio système (questions d'entretien posées via Zoom, Teams, Meet…), les envoie à Gemini, et affiche les réponses suggérées dans une fenêtre **invisible lors d'un partage d'écran**.

---

## 2. Stack technique

| Couche | Technologie | Rôle |
|---|---|---|
| Capture audio | `sounddevice` | Accès WASAPI loopback sans plugin C++ |
| Encodage audio | `wave` + `io.BytesIO` | PCM brut → WAV en mémoire |
| Modèle IA | Gemini 1.5 Flash | Analyse audio → réponse texte |
| SDK IA | `google-generativeai` | Appels à l'API Gemini |
| Interface UI | `PyQt6` | Fenêtre flottante minimaliste |
| Invisibilité | `ctypes` (WinAPI) | Masquer la fenêtre aux screen recorders |
| Threading | `threading` (stdlib) | Capture audio en arrière-plan |

---

## 3. Architecture

```
Audio système (speakers / casque)
           ↓
  sounddevice — WASAPI loopback
           ↓
  Chunk PCM 16-bit, 44100 Hz, 3 s
           ↓
  Encode WAV  →  io.BytesIO
           ↓
  google-generativeai
           ↓
  Gemini 1.5 Flash
  (audio + prompt)
           ↓
  Réponse texte
           ↓
  PyQt6 — fenêtre flottante
  WDA_EXCLUDEFROMCAPTURE
```

---

## 4. Structure des fichiers

```
interview-assistant/
├── main.py               # Point d'entrée, boucle principale
├── audio_capture.py      # Capture WASAPI + encodage WAV
├── gemini_client.py      # Appels à l'API Gemini
├── ui/
│   └── window.py         # Fenêtre PyQt6 + invisibilité
├── utils/
│   └── win_api.py        # ctypes — SetWindowDisplayAffinity
├── requirements.txt
└── .env                  # GOOGLE_API_KEY (ne pas commit)
```

---

## 5. Code — composants principaux

### 5.1 Capture audio (`audio_capture.py`)

```python
import sounddevice as sd
import numpy as np
import io, wave

SAMPLERATE = 44100
CHANNELS   = 2
CHUNK_SEC  = 3          # secondes par chunk envoyé à Gemini


def list_loopback_devices():
    """Affiche les devices disponibles pour choisir le bon loopback."""
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            print(f"[{i}] {d['name']}")


def capture_chunk(device_index: int = None) -> bytes:
    """Capture CHUNK_SEC secondes d'audio système, retourne un buffer WAV."""
    audio = sd.rec(
        frames=SAMPLERATE * CHUNK_SEC,
        samplerate=SAMPLERATE,
        channels=CHANNELS,
        dtype='int16',
        device=device_index,
        blocking=True
    )
    return _encode_wav(audio)


def _encode_wav(pcm: np.ndarray) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)          # int16 = 2 octets
        wf.setframerate(SAMPLERATE)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()
```

> **Tip :** lancer `list_loopback_devices()` une fois pour trouver l'index du device  
> *Stereo Mix* ou *Loopback* selon la carte son.

---

### 5.2 Client Gemini (`gemini_client.py`)

```python
import google.generativeai as genai
import base64, os

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
_model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """
Tu es un assistant d'entretien technique discret.
Si tu entends une question technique dans l'audio, fournis une réponse
concise et directement utilisable (3 à 5 phrases max), en français.
Si tu n'entends aucune question claire, réponds uniquement : NO_QUESTION
"""


def analyze_audio(wav_bytes: bytes) -> str | None:
    """Envoie un buffer WAV à Gemini. Retourne la réponse ou None."""
    audio_b64 = base64.b64encode(wav_bytes).decode()
    response = _model.generate_content([
        {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}},
        SYSTEM_PROMPT
    ])
    text = response.text.strip()
    return None if text == "NO_QUESTION" else text
```

---

### 5.3 Fenêtre PyQt6 (`ui/window.py`)

```python
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore    import Qt, pyqtSignal
from utils.win_api   import hide_from_screen_capture


class AssistantWindow(QWidget):
    answer_ready = pyqtSignal(str)   # signal thread-safe

    def __init__(self):
        super().__init__()
        self._build_ui()
        self.answer_ready.connect(self._show_answer)

    def _build_ui(self):
        self.setWindowTitle("Interview Assistant")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint  |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(480, 220)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)

        self.status = QLabel("En écoute…")
        self.status.setStyleSheet("color: #888; font-size: 12px;")

        self.answer = QLabel("")
        self.answer.setWordWrap(True)
        self.answer.setStyleSheet(
            "background: rgba(20,20,20,0.88); color: #f0f0f0;"
            "font-size: 14px; padding: 12px; border-radius: 8px;"
        )

        layout.addWidget(self.status)
        layout.addWidget(self.answer)
        self.setLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        hide_from_screen_capture(hwnd)    # appliqué dès l'affichage

    def _show_answer(self, text: str):
        self.status.setText("Réponse suggérée")
        self.answer.setText(text)
```

---

### 5.4 API Windows (`utils/win_api.py`)

```python
import ctypes

WDA_EXCLUDEFROMCAPTURE = 0x00000011   # Windows 10 build 2004+


def hide_from_screen_capture(hwnd: int):
    """Rend la fenêtre invisible dans les screen recorders (Zoom, Teams, OBS…)."""
    result = ctypes.windll.user32.SetWindowDisplayAffinity(
        hwnd,
        WDA_EXCLUDEFROMCAPTURE
    )
    if not result:
        print("[warn] SetWindowDisplayAffinity a échoué — Windows trop ancien ?")
```

---

### 5.5 Point d'entrée (`main.py`)

```python
import sys, threading
from PyQt6.QtWidgets import QApplication
from audio_capture   import capture_chunk
from gemini_client   import analyze_audio
from ui.window       import AssistantWindow


def capture_loop(window: AssistantWindow):
    """Tourne en continu dans un thread background."""
    while True:
        try:
            wav   = capture_chunk()
            reply = analyze_audio(wav)
            if reply:
                window.answer_ready.emit(reply)   # signal thread-safe
        except Exception as e:
            print(f"[erreur] {e}")


if __name__ == "__main__":
    app    = QApplication(sys.argv)
    window = AssistantWindow()
    window.show()

    t = threading.Thread(target=capture_loop, args=(window,), daemon=True)
    t.start()

    sys.exit(app.exec())
```

---

## 6. Dépendances (`requirements.txt`)

```txt
sounddevice>=0.4.6
numpy>=1.24
PyQt6>=6.5.0
google-generativeai>=0.5.0
python-dotenv>=1.0.0
```

Installation :

```bash
pip install -r requirements.txt
```

---

## 7. Configuration (`.env`)

```env
GOOGLE_API_KEY=AIza...votre_clé_ici
```

Charger dans `main.py` :

```python
from dotenv import load_dotenv
load_dotenv()
```

> Ne jamais commiter le fichier `.env`. Ajouter `.env` dans `.gitignore`.

---

## 8. Roadmap

### Phase 1 — MVP (Jours 1–3)
- [ ] Capture audio WASAPI avec `sounddevice`
- [ ] Encodage WAV en mémoire (`io.BytesIO`)
- [ ] Appel Gemini 1.5 Flash avec buffer audio
- [ ] Affichage de la réponse dans la fenêtre Qt
- [ ] Thread de capture indépendant

### Phase 2 — Finitions (Jours 4–5)
- [ ] `WDA_EXCLUDEFROMCAPTURE` appliqué au démarrage
- [ ] Filtre `NO_QUESTION` pour éviter les appels inutiles
- [ ] Détection d'énergie RMS pour sauter les silences
- [ ] Sélecteur de device audio au premier lancement
- [ ] Gestion des erreurs API (quota, timeout, réseau)

### Phase 3 — Améliorations futures
- [ ] Passer à la Gemini Live API (streaming audio continu)
- [ ] Raccourci clavier global (pause / reprise)
- [ ] Historique de la session exportable en PDF
- [ ] Mode texte : l'utilisateur tape la question manuellement
- [ ] Packaging `.exe` avec PyInstaller

---

## 9. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| Mauvais device WASAPI | Silence capturé | Sélecteur de device au 1er lancement |
| Latence Gemini (1–3 s) | Réponse en retard | Chunks de 2–3 s + Gemini Live API à terme |
| `WDA_EXCLUDEFROMCAPTURE` non supporté | Fenêtre visible | Vérifier la version Windows au démarrage |
| Faux positifs (musique, notification) | Appels API inutiles | Filtre RMS avant envoi |
| Quota API dépassé | Aucune réponse | Message d'erreur clair + retry exponentiel |

---

## 10. Références

- [sounddevice — WASAPI loopback](https://python-sounddevice.readthedocs.io/en/latest/usage.html#device-selection)
- [Google Generative AI Python SDK](https://github.com/google-gemini/generative-ai-python)
- [Gemini Live API (preview)](https://ai.google.dev/api/live)
- [SetWindowDisplayAffinity — Microsoft Docs](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowdisplayaffinity)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)