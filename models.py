from pydantic import BaseModel
from typing import List, Optional, Literal
from enum import Enum

class RecordingStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Utterance(BaseModel):
    start: float
    end: float
    text: str
    speaker: str

class SOAPEntry(BaseModel):
    text: str
    source_indices: List[int]

class SOAPSection(BaseModel):
    name: Literal["Subjective", "Objective", "Assessment", "Plan"]
    entries: List[SOAPEntry]

class SOAPNote(BaseModel):
    sections: List[SOAPSection]

class Recording(BaseModel):
    id: str
    status: RecordingStatus
    audio_path: Optional[str] = None
    transcript: Optional[List[Utterance]] = None
    soap_note: Optional[SOAPNote] = None
    error: Optional[str] = None