import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List
import logging
import os
from models import Utterance
import asyncio

logger = logging.getLogger(__name__)

class AssemblyAITranscriber:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.assemblyai.com/v2"
        self.timeout = httpx.Timeout(float(os.getenv("HTTP_CLIENT_TIMEOUT", "900")))
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def transcribe(self, file_path: str) -> List[Utterance]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"authorization": self.api_key}
                
                # Upload file
                with open(file_path, "rb") as f:
                    upload_response = await client.post(
                        f"{self.base_url}/upload",
                        headers=headers,
                        files={"file": f}
                    )
                upload_response.raise_for_status()
                upload_url = upload_response.json()["upload_url"]
                
                # Start transcription
                transcript_response = await client.post(
                    f"{self.base_url}/transcript",
                    json={
                        "audio_url": upload_url,
                        "speaker_labels": True,
                        "auto_highlights": True
                    },
                    headers=headers
                )
                transcript_response.raise_for_status()
                transcript_id = transcript_response.json()["id"]
                
                # Poll for results
                while True:
                    polling_response = await client.get(
                        f"{self.base_url}/transcript/{transcript_id}",
                        headers=headers
                    )
                    polling_response.raise_for_status()
                    status = polling_response.json()["status"]
                    
                    if status == "completed":
                        return self._parse_response(polling_response.json())
                    elif status == "error":
                        raise Exception(polling_response.json()["error"])
                    
                    await asyncio.sleep(5)
        
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

    def _parse_response(self, response: dict) -> List[Utterance]:
        utterances = []
        for utterance in response.get("utterances", []):
            utterances.append(Utterance(
                start=utterance["start"] / 1000,
                end=utterance["end"] / 1000,
                text=utterance["text"],
                speaker=utterance["speaker"]  # Now accepts string speaker labels
            ))
        return utterances