🎙️ VoiceChat AI – Asistente de voz inteligente con Flask + Angular

VoiceChat AI es una aplicación completa (frontend + backend) que permite mantener una conversación natural por voz con un modelo de lenguaje local (LM Studio o DeepSeek).
El usuario habla → el sistema transcribe el audio → genera una respuesta con IA → la devuelve en audio y texto al chat web.

🚀 Características principales
🧠 Backend (Flask)

Reconocimiento de voz (STT) usando faster-whisper
 para transcribir el audio del usuario.

Generación de respuesta con IA a través de una API local (por ejemplo, LM Studio o DeepSeek-V3).

Conversión de texto a voz (TTS) con edge-tts
 y caché local de archivos .mp3.

API REST con endpoints:

POST /stt → convierte audio (.webm/.wav) en respuesta de voz.

POST /tts → genera voz a partir de texto.

GET /media/<id>.mp3 → sirve los audios cacheados.

CORS habilitado para integración directa con el frontend.

Compatibilidad con GPU (CUDA) opcional para acelerar Whisper.

💻 Frontend (Angular 17)

Interfaz tipo chat con mensajes de audio y texto.

Grabación directa desde el micrófono mediante MediaRecorder.

Reproducción automática de las respuestas del asistente.

Indicadores visuales:

Loader “Enviando…” mientras se procesa la petición.

Mensaje de estado mientras el backend genera la respuesta.

Arquitectura reactiva con signals (@if, @for, etc. de Angular 17).

Diseño limpio con TailwindCSS.

🧩 Estructura del proyecto
VoiceChatAI/
│
├── frontend/                 # Angular 17 app
│   ├── src/app/
│   │   ├── components/
│   │   ├── services/
│   │   └── pages/
│   └── ...
│
├── backend/
│   ├── app.py                # Servidor Flask principal
│   ├── analisisvoz.py        # Lógica STT + TTS + LLM
│   ├── tts_cache/            # Carpeta donde se guardan los .mp3
│   ├── requirements.txt
│   └── .env
│
└── README.md

⚙️ Instalación
🔹 Backend (Flask)
# Crear entorno
conda create -n voicechat python=3.10
conda activate voicechat

# Instalar dependencias
pip install -r requirements.txt

# (opcional) Instalar ffmpeg si no lo tienes
conda install -c conda-forge ffmpeg

# Iniciar servidor
python app.py


El backend correrá en http://localhost:8000.

🔹 Frontend (Angular)
cd frontend
npm install
ng serve


El frontend se servirá en http://localhost:4200.

🗣️ Flujo de funcionamiento

El usuario graba un audio en el navegador.

El frontend envía el Blob al backend (/stt).

Flask:

Convierte el audio a WAV (ffmpeg).

Lo transcribe con Whisper.

Envía el texto al modelo de LM Studio.

Genera una respuesta hablada con Edge TTS.

El frontend recibe el .mp3 resultante y lo reproduce en el chat.

🧠 Tecnologías utilizadas
Categoría	Herramienta
Frontend	Angular 17, TypeScript, TailwindCSS
Backend	Flask, Flask-CORS
STT	faster-whisper
TTS	edge-tts, pyttsx3
AI	LM Studio / DeepSeek
Audio	ffmpeg, pydub
Infraestructura	Python 3.10+, Conda
📦 Próximas mejoras

Soporte multilenguaje (en-US, es-ES, pt-BR).

Persistencia de historial de conversación.

Selección de voz TTS y velocidad desde el frontend.

Compatibilidad con APIs externas (OpenAI, Gemini...).

🧑‍💻 Autor

Aarón Borrego
Desarrollador full stack • IA, voz e interfaces naturales
📧 borregomagantoaaron@gmail.com
