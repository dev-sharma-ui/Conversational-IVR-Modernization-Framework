# ============================================================
# INSTALLATION GUIDE — READ THIS BEFORE pip install
# ============================================================

## STEP 1 — Install PyTorch (CPU-only, much smaller ~250MB)
## This MUST be done BEFORE pip install -r requirements.txt

### Windows / macOS / Linux (CPU only — recommended for most users):
pip install torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu

### If above fails, use latest stable:
pip install torch --index-url https://download.pytorch.org/whl/cpu

### Only if you have an NVIDIA GPU and CUDA installed:
pip install torch==2.3.0

---

## STEP 2 — Install core requirements
pip install -r requirements.txt

---

## STEP 3 — Download spaCy language model
python -m spacy download en_core_web_sm

---

## STEP 4 — (OPTIONAL) Server-side Whisper STT
## Only needed if you want to use file upload audio instead of browser mic
## The frontend uses Web Speech API by default (no server model needed)

pip install faster-whisper==1.0.1

## Also requires ffmpeg system package:
## Windows: winget install ffmpeg   OR   choco install ffmpeg
## macOS:   brew install ffmpeg
## Ubuntu:  sudo apt install ffmpeg

---

## STEP 5 — Run the server
cd Project
uvicorn main:app --reload --port 8000

---

## COMMON ERRORS:

## Error: "No module named 'torch'"
## Fix:  pip install torch --index-url https://download.pytorch.org/whl/cpu

## Error: "OSError: [E050] Can't find model 'en_core_web_sm'"
## Fix:  python -m spacy download en_core_web_sm

## Error: "ctranslate2 not found" or faster-whisper install fails
## Fix:  pip install ctranslate2 faster-whisper
##       The frontend already uses browser Web Speech API so Whisper is optional.

## Error: torch install very slow or fails
## Fix:  Use CPU-only install: pip install torch --index-url https://download.pytorch.org/whl/cpu
