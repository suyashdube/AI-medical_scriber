import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from models import SOAPNote, Utterance, SOAPEntry, SOAPSection
import logging
import re
from typing import List

logger = logging.getLogger(__name__)

class GeminiSoapGenerator:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.generation_config = {
            "temperature": 0.2,  # More deterministic for medical notes
            "max_output_tokens": 2000,
            "top_p": 0.8
        }
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_soap_note(self, utterances: List[Utterance]) -> SOAPNote:
        try:
            formatted_transcript = self._format_transcript(utterances)
            prompt = self._create_prompt(formatted_transcript)
            
            response = await self.model.generate_content_async(prompt)
            
            if not response.text:
                raise ValueError("Empty response from Gemini")
                
            return self._parse_response(response.text)
        
        except Exception as e:
            logger.error(f"SOAP generation failed: {str(e)}")
            raise

    def _format_transcript(self, utterances: List[Utterance]) -> str:
        return "\n".join(
            f"[{i}] [Speaker {u.speaker}] [{u.start:.1f}-{u.end:.1f}s]: {u.text}"
            for i, u in enumerate(utterances)
        )

    def _create_prompt(self, transcript: str) -> str:
        return f"""Generate a structured SOAP note from this medical conversation. 
        Include references to transcript segments using their [numbers] in square brackets.
        Use exactly this format:

        Subjective:
        - [Patient reported chest pain starting 2 hours ago] [0,3]
        - [Denies history of cardiac issues] [5]

        Objective:
        - [BP 150/95, HR 110] [12]
        - [Lungs clear to auscultation] [14]

        Assessment:
        - [Probable acute coronary syndrome] [15,18]

        Plan:
        - [ECG and cardiac enzymes ordered] [20]
        - [Aspirin 325mg administered] [22]

        Transcript:
        {transcript}"""

    def _parse_response(self, text: str) -> SOAPNote:
        sections = []
        current_section = None
        
        # Split by section headers
        parts = re.split(r"^(Subjective|Objective|Assessment|Plan):", text, flags=re.MULTILINE)
        
        for i in range(1, len(parts), 2):
            section_name = parts[i]
            content = parts[i+1].strip()
            
            entries = []
            for line in content.split("\n"):
                line = line.strip()
                if not line or not line.startswith("-"):
                    continue
                
                # Remove bullet point
                line = line[1:].strip()
                
                # Extract references
                ref_matches = re.finditer(r"\[(\d+(?:,\s*\d+)*)\]", line)
                ref_indices = []
                clean_line = line
                
                for match in ref_matches:
                    indices = [int(idx) for idx in match.group(1).split(",")]
                    ref_indices.extend(indices)
                    clean_line = clean_line.replace(match.group(0), "").strip()
                
                if clean_line:
                    entries.append(SOAPEntry(
                        text=clean_line,
                        source_indices=ref_indices
                    ))
            
            sections.append(SOAPSection(
                name=section_name,
                entries=entries
            ))
        
        return SOAPNote(sections=sections)