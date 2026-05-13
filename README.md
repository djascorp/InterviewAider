# InterviewAider

Assistant d'entretien technique en temps reel. Capture l'audio systeme (Zoom, Teams, Meet...), detecte les questions techniques via Gemini, et affiche les reponses suggerees dans un overlay invisible lors du partage d'ecran.

## Fonctionnalites

- **Capture audio WASAPI loopback** - ecoute l'audio systeme via Stereo Mix / Loopback
- **Detection vocale (VAD)** - segmentation intelligente de la parole avec webrtcvad et bruit adaptatif
- **Analyse Gemini** - detection de questions techniques et generation de reponses structurees
- **Overlay invisible** - fenetre masquee des screen recorders via `SetWindowDisplayAffinity` (Windows 10 build 2004+)
- **Raccourcis globaux** - pause/reprise, repli, toggle visibilite
- **System tray** - icone dans la barre des taches
- **Historique** - navigation dans les reponses precedentes

## Prerequis

- **OS** : Windows 10 (build 2004+) ou Windows 11
- **Python** : 3.10 ou superieur
- **Audio** : peripherique Stereo Mix / WASAPI Loopback active
- **API** : cle Google Gemini (`GOOGLE_API_KEY`)

## Installation

```bash
# Cloner le depot
git clone https://github.com/djascorp/InterviewAider.git
cd InterviewAider

# Creer un environnement virtuel
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS

# Installer les dependances
pip install -r requirements.txt
```

## Configuration

Creer un fichier `.env` a la racine du projet :

```env
GOOGLE_API_KEY=AIza...votre_cle_ici
```

Un fichier `.env.example` est fourni comme modele.

## Utilisation

```bash
python main.py
```

1. Au lancement, un dialogue vous demande de selectionner le peripherique audio (choisissez Stereo Mix ou Loopback)
2. L'overlay flottant apparait en haut a droite de l'ecran
3. Les questions techniques detectees dans l'audio sont automatiquement analysees
4. Les reponses s'affichent dans l'overlay

## Raccourcis clavier

| Raccourci | Action |
|---|---|
| `Ctrl+Alt+Space` | Pause / Reprise |
| `Ctrl+Alt+H` | Replier / Deployer l'overlay |
| `Ctrl+Alt+V` | Afficher / Masquer la fenetre |

## Structure du projet

```
InterviewAider/
├── main.py                # Point d'entree
├── audio_capture.py       # Capture audio WASAPI + VAD + segmentation
├── gemini_client.py       # Client API Gemini (analyse audio)
├── ui/
│   ├── window.py          # Fenetre overlay PyQt6
│   ├── widgets.py         # Composants UI (header, waveform, etats)
│   ├── dialogs.py         # Dialogues (selection device, tray icon)
│   └── overlay_styles.py  # Theme et constantes visuelles
├── utils/
│   ├── win_api.py         # SetWindowDisplayAffinity (invisibilite)
│   └── global_hotkeys.py  # Raccourcis clavier globaux (WinAPI)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Stack technique

| Couche | Technologie |
|---|---|
| Capture audio | `sounddevice` (WASAPI loopback) |
| Detection vocale | `webrtcvad` + energie adaptative |
| Modele IA | Google Gemini (`gemini-3-flash-preview`) |
| Interface | `PyQt6` (overlay flottant) |
| Invisibilite | `ctypes` WinAPI (`SetWindowDisplayAffinity`) |

## Licence

Ce projet est distribue sous licence **Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0)**. Usage non-commercial uniquement. Pour une licence commerciale, contactez l'auteur. Voir le fichier [LICENSE](LICENSE).
