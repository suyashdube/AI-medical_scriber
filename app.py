import logging
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid
import os
from dotenv import load_dotenv
from services.transcriber import AssemblyAITranscriber  
from services.ai import GeminiSoapGenerator
from models import Recording, Utterance, SOAPNote
import asyncio

load_dotenv()

app = FastAPI()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# In-memory storage (replace with database in production)
recordings: Dict[str, Recording] = {}

# Services - Updated to use AssemblyAI
transcriber = AssemblyAITranscriber(os.getenv("ASSEMBLYAI_API_KEY"))
ai_service = GeminiSoapGenerator(os.getenv("GOOGLE_API_KEY"))

class StartRecordingResponse(BaseModel):
    recording_id: str

class ProcessFileResponse(BaseModel):
    recording_id: str
    status: str

@app.post("/record/start", response_model=StartRecordingResponse)
async def start_recording():
    recording_id = str(uuid.uuid4())
    recordings[recording_id] = Recording(
        id=recording_id,
        status="created"
    )
    return {"recording_id": recording_id}

@app.post("/process-file")
async def process_audio_file(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...)
):
    # Validate file type
    if not audio_file.filename.lower().endswith(('.wav', '.mp3', '.mp4', '.m4a')):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload WAV, MP3, MP4, or M4A"
        )

    recording_id = str(uuid.uuid4())
    recordings[recording_id] = Recording(
        id=recording_id,
        status="processing"
    )
    
    # Save audio file temporarily
    file_path = f"audio/{recording_id}{os.path.splitext(audio_file.filename)[1]}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        with open(file_path, "wb") as f:
            while chunk := await audio_file.read(1024 * 1024):  # 1MB chunks
                f.write(chunk)
    except Exception as e:
        logger.error(f"Error saving audio: {str(e)}")
        recordings[recording_id].status = "failed"
        recordings[recording_id].error = str(e)
        raise HTTPException(status_code=500, detail="Error saving audio file")
    
    background_tasks.add_task(process_recording, recording_id, file_path)
    return {"recording_id": recording_id, "status": "processing_started"}

async def process_recording(recording_id: str, file_path: str):
    try:
        # Transcribe audio with timeout
        utterances = await asyncio.wait_for(
            transcriber.transcribe(file_path),
            timeout=float(os.getenv("TRANSCRIPTION_TIMEOUT", "600"))  # 10 minutes
        )
        
        recordings[recording_id].transcript = utterances
        
        # Generate SOAP note with timeout
        soap_note = await asyncio.wait_for(
            ai_service.generate_soap_note(utterances),
            timeout=float(os.getenv("SOAP_GENERATION_TIMEOUT", "300"))  # 5 minutes
        )
        
        recordings[recording_id].soap_note = soap_note
        recordings[recording_id].status = "completed"
        
    except asyncio.TimeoutError:
        logger.error("Processing timed out")
        recordings[recording_id].status = "failed"
        recordings[recording_id].error = "Processing timed out"
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        recordings[recording_id].status = "failed"
        recordings[recording_id].error = str(e)
    finally:
        # Clean up audio file
        try:
            os.remove(file_path)
        except OSError as e:
            logger.error(f"Error removing audio file: {str(e)}")

@app.get("/soap-note/{recording_id}", response_model=SOAPNote)
async def get_soap_note(recording_id: str):
    recording = recordings.get(recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    if recording.status == "failed":
        raise HTTPException(status_code=500, detail=recording.error)
    if recording.status != "completed":
        raise HTTPException(status_code=425, detail="Processing not complete")
    return recording.soap_note

@app.get("/status/{recording_id}")
async def get_status(recording_id: str):
    recording = recordings.get(recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return {"status": recording.status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)