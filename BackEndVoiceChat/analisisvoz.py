

from faster_whisper import WhisperModel
import speech_recognition as sr
import requests  # Librería para hacer solicitudes HTTP (acceder al endpoint de LlmStudio)
import speech_recognition as sr
import pyttsx3
import json, os,tempfile, subprocess
import os
from dotenv import load_dotenv
import os, hashlib, tempfile
from flask import Flask, request, send_file, abort
from flask_cors import CORS
import pyttsx3
import asyncio, edge_tts, tempfile, os

load_dotenv()
# Configuración de la URL y el modelo de LlmStudio local
LLMSTUDIO_URL = os.getenv("LLMSTUDIO_URL")  # Endpoint del servidor LlmStudio
LLMSTUDIO_MODEL = os.getenv("LLMSTUDIO_MODEL")  # Nombre del modelo definido en LlmStudio


HISTORY_FILE = "chat_history.json"


# Memoria mínima por turnos
CHAT_HISTORY = []  # lista de dicts [{"role":"user"/"assistant","content": "..."}]
N_TURNS = 6  # número de turnos a recordar
SYSTEM_PROMPT = (
    "Respondes SIEMPRE en español (es-ES), breve y natural. "
    "No muestres razonamientos ni etiquetas especiales."
)

HISTORY_FILE = "./chat_history.json"

MODEL = "small"  # o "base" si quieres aún menos consumo
try:
    model = WhisperModel(MODEL, device="cuda", compute_type="float16")
except Exception as e:
    print("[Whisper] GPU no disponible, uso CPU:", e)
    model = WhisperModel(MODEL, device="cpu", compute_type="int8")

def load_history() -> list:
    """Carga historial; si el archivo está vacío/corrupto, devuelve [] y guarda copia .bak."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            raw = f.read()
        if not raw.strip():  # archivo vacío
            return []
        data = json.loads(raw)
        # Validación mínima
        if isinstance(data, list):
            return data
        # Si no es lista, lo tratamos como corrupto
        raise ValueError("Historial no es lista")
    except Exception as e:
        # Haz backup del archivo problemático y empieza fresco
        try:
            bak = HISTORY_FILE + ".bak"
            if os.path.exists(bak):
                os.remove(bak)
            os.replace(HISTORY_FILE, bak)
            print(f"[HIST] Archivo corrupto: movido a {bak} ({e})")
        except Exception:
            pass
        return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def ask_llm(user_text: str) -> str:
    CHAT_HISTORY = load_history()
    # ... después de obtener respuesta:
    CHAT_HISTORY.append({"role": "user", "content": user_text})
    save_history(CHAT_HISTORY)
    # construye ventana (system + últimos N)
    msgs = [{"role":"system","content": SYSTEM_PROMPT}] + CHAT_HISTORY[-N_TURNS:]
    # llama a tu API (reusa tu función cambiando para aceptar messages)
    response = call_llmstudio_api_with_messages(msgs)  # ver función abajo

    # 5) añade respuesta del asistente y guarda
    CHAT_HISTORY.append({"role": "assistant", "content": response})
    save_history(CHAT_HISTORY)
    return response

def call_llmstudio_api_with_messages(messages, temperature=0.5):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": LLMSTUDIO_MODEL,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.9,
        "max_tokens": 256,
        "stream": False
    }
    resp = requests.post(LLMSTUDIO_URL, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return (data["choices"][0]["message"]["content"] or "").strip() or "Entendido."

def pick_spanish_voice(engine: pyttsx3.Engine):
    for v in engine.getProperty("voices"):
        name = (getattr(v, "name", "") or "").lower()
        vid  = (getattr(v, "id", "") or "").lower()
        if "spanish" in name or "es_" in vid or "es-" in vid or vid == "es":
            return v.id
    return None

# --- TTS (pyttsx3) ---
def init_tts():
    engine = pyttsx3.init()
    # Intenta seleccionar una voz en español
    selected_voice = None
    vid = pick_spanish_voice(engine)
    if vid:
        engine.setProperty("voice", vid)
    # Ajustes recomendados
    engine.setProperty("rate", 170)   # velocidad (ajusta al gusto)
    engine.setProperty("volume", 1.0) # volumen 0.0–1.0
    return engine


def speak(text: str, _tts_engine):
    if not text:
        return
    _tts_engine.say(text)
    _tts_engine.runAndWait()



async def synth_to_mp3_edge(text: str, voice: str = "es-ES-ElviraNeural", rate: str = "+0%", pitch: str = "+0Hz"):
    """Genera un MP3 temporal con Edge TTS y devuelve su ruta."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.close()
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(tmp.name)
    return tmp.name



def cache_key(text: str, rate: int, voice_id: str | None) -> str:
    h = hashlib.sha1()
    h.update(text.encode("utf-8"))
    h.update(f"|rate={rate}".encode("utf-8"))
    h.update(f"|voice={voice_id or 'auto-es'}".encode("utf-8"))
    return h.hexdigest()


app = Flask(__name__)
CORS(
    app,
    resources={
        r"/stt": {"origins": ["http://localhost:4200"]},
        r"/tts": {"origins": ["http://localhost:4200"]},
        r"/tts_cache/*": {"origins": ["http://localhost:4200"]},
    },
    supports_credentials=False,  # pon True solo si usas cookies/autorización con credenciales
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Disposition"]
)
# Ruta absoluta del directorio donde está este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carpeta tts_cache dentro del proyecto
CACHE_DIR = os.path.join(BASE_DIR, "tts_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def cache_key(text: str, voice: str) -> str:
    return hashlib.sha1(f"{voice}|{text}".encode("utf-8")).hexdigest()

@app.get("/tts")
def tts():
    data = request.get_json(silent=True) if request.is_json else None
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    voice = data.get("voice", "es-ES-ElviraNeural").strip()
    print("Llamando al modelo LlmStudio...")
    try:
        response = ask_llm(text)
    except Exception as e:
        print("Error al llamar a LlmStudio: {0}".format(e))
    if not response:
        return abort(400, "Falta ?text=")
    if len(response) > 2000:
        return abort(413, "Texto demasiado largo")

    key = cache_key(response, voice)
    mp3_path = os.path.join(CACHE_DIR, f"{key}.mp3")

    if not os.path.exists(mp3_path):
        print(f"[TTS] Generando nuevo audio con voz {voice}")
        mp3_tmp = asyncio.run(synth_to_mp3_edge(response, voice, "+170%"))
        os.replace(mp3_tmp, mp3_path)
        
    return send_file(mp3_path, mimetype="audio/mpeg", as_attachment=False, download_name="tts.mp3")



def ffmpeg_convert_to_wav16k_mono(in_path: str, out_path: str):
    """
    Convierte cualquier contenedor de audio (webm/ogg/mp3/wav) a WAV PCM 16 kHz mono usando ffmpeg local.
    Compatible con Windows 10/11 64 bits.
    """
    # Ruta local de ffmpeg (ajústala si lo pusiste en otra carpeta)
    ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"

    # Si no existe en esa ruta, intentamos usar el que esté en PATH
    if not os.path.exists(ffmpeg_path):
        ffmpeg_path = "ffmpeg"

    # Añadimos la carpeta de ffmpeg al PATH del proceso (por si acaso)
    os.environ["PATH"] = os.pathsep.join([
        os.path.dirname(ffmpeg_path),
        os.environ.get("PATH", "")
    ])

    # Construimos el comando de forma segura
    cmd = [
        ffmpeg_path,
        "-y",              # sobrescribir salida sin preguntar
        "-loglevel", "error",
        "-i", in_path,
        "-ac", "1",        # mono
        "-ar", "16000",    # 16 kHz
        "-f", "wav",
        out_path
    ]

    # Ejecutamos FFmpeg
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Convertido correctamente a {out_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al convertir audio con FFmpeg: {e}")
        raise

@app.post("/stt")
def stt():
    voice = "es-ES-ElviraNeural"
    # Acepta multipart/form-data con campo "audio"
    if "audio" not in request.files:
        abort(400, "Falta archivo 'audio' (multipart/form-data)")
    f = request.files["audio"]
    if not f.filename:
        abort(400, "Archivo sin nombre")

    # Guarda Blob temporalmente
    src = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(f.filename)[1] or ".webm")
    src.write(f.read()); src.close()

    # Convierte a WAV 16k mono
    wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav"); wav.close()
    try:
        ffmpeg_convert_to_wav16k_mono(src.name, wav.name)
    except subprocess.CalledProcessError as e:
        try: os.remove(src.name)
        except: pass
        abort(415, f"Error al convertir audio: {e}")

    # Transcribe (español)
    try:
        segments, info = model.transcribe(wav.name, language="es", vad_filter=True)
        text = "".join(seg.text for seg in segments).strip()
    finally:
        # Limpieza de temporales
        try: os.remove(src.name); os.remove(wav.name)
        except: pass

    print("Llamando al modelo LlmStudio...")
    try:
        response = ask_llm(text)
    except Exception as e:
        print("Error al llamar a LlmStudio: {0}".format(e))
    if not response:
        return abort(400, "Falta ?text=")
    if len(response) > 2000:
        return abort(413, "Texto demasiado largo")

    key = cache_key(response, voice)
    mp3_path = os.path.join(CACHE_DIR, f"{key}.mp3")

    if not os.path.exists(mp3_path):
        print(f"[TTS] Generando nuevo audio con voz {voice}")
        mp3_tmp = asyncio.run(synth_to_mp3_edge(response, voice))
        os.replace(mp3_tmp, mp3_path)
    return send_file(mp3_path, mimetype="audio/mpeg", as_attachment=False, download_name="tts.mp3")

    

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)

