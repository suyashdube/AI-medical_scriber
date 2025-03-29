
# AI Medical Scribe System

An automated SOAP note generator that transforms doctor-patient conversations into structured clinical notes using AssemblyAI for transcription and Google Gemini for medical note generation.

## Key Features

- **Audio Processing**: Handles 30-40 minute medical conversations
- **SOAP Note Generation**: Creates Subjective, Objective, Assessment, Plan sections
- **Traceability**: Maps every note line to source conversation segments
- **Clinician Review**: Supports hover-to-verify source dialogue

## System Architecture

```mermaid
graph LR
    A[Audio Input] --> B[AssemblyAI Transcription]
    B --> C[Gemini SOAP Generation]
    C --> D[Web Interface]
    D --> E[Clinician Feedback]
    E --> F[Model Improvement]
```
Prerequisites:
- Python 3.10+
- Google Cloud account (for Gemini API)
- AssemblyAI account

## Setup
- git clone https://github.com/your-repo/medical-scribe.git
- cd medical-scribe

- pip install -r requirements.txt
- cp .env.example .env
- edit env:
  - ASSEMBLYAI_API_KEY=your_key_here
  - GOOGLE_API_KEY=your_key_here

## start the server
uvicorn app:app --reload --port 8000

- go to http://localhost:8000/docs

- Use "Try it out" on /process-file endpoint

- Upload a sample medical conversation

## Endpoints
Endpoints:

- POST /process-file - Upload audio (WAV/MP3)

- GET /soap-note/{id} - Retrieve generated SOAP note

- GET /status/{id} - Check processing status

## Sample soap-note generated
```json

{
  "sections": [
    {
      "name": "Subjective",
      "entries": [
        {
          "text": "[Patient reported feeling tired and that her blood pressure is always racing]",
          "source_indices": [
            1,
            87
          ]
        },
        {
          "text": "[Denies chest pain]",
          "source_indices": [
            65,
            153,
            237
          ]
        },
        {
          "text": "[Reports ankle swelling]",
          "source_indices": [
            67,
            155,
            239
          ]
        },
        {
          "text": "[Reports dizziness, particularly when getting up quickly]",
          "source_indices": [
            73,
            161,
            245
          ]
        },
        {
          "text": "[Reports excessive thirst and urination, attributed to high water intake]",
          "source_indices": [
            77,
            165,
            249
          ]
        },
        {
          "text": "[Reports a history of diabetes and hypertension in her family]",
          "source_indices": [
            23,
            31,
            33,
            109,
            117,
            119
          ]
        },
        {
          "text": "[Reports previous treatment for high blood pressure, but doesn't remember medication details]",
          "source_indices": [
            37,
            125
          ]
        },
        {
          "text": "[Reports hives, possibly stress-related, with a known dairy allergy]",
          "source_indices": [
            51,
            139
          ]
        },
        {
          "text": "[Takes over-the-counter Zyrtec for hives]",
          "source_indices": [
            53,
            141
          ]
        },
        {
          "text": "[Denies history of cancer, asthma, or other significant medical issues besides high blood pressure]",
          "source_indices": [
            29,
            115,
            203
          ]
        },
        {
          "text": "[Expresses concern about previous doctor's potential cognitive impairment and desire to start fresh with diagnosis]",
          "source_indices": [
            79,
            167,
            251
          ]
        }
      ]
    },
    {
      "name": "Objective",
      "entries": [
        {
          "text": "No vital signs explicitly mentioned in the transcript.",
          "source_indices": []
        }
      ]
    },
    {
      "name": "Assessment",
      "entries": [
        {
          "text": "[Hypertension]   The patient reports feeling like her blood pressure is always racing.",
          "source_indices": [
            1,
            87
          ]
        },
        {
          "text": "[Possible secondary causes of hypertension need to be investigated due to family history of diabetes and hypertension,  weight issues, and patient's request to start fresh with diagnosis. ]",
          "source_indices": [
            23,
            31,
            33,
            79,
            109,
            117,
            119,
            167,
            251
          ]
        }
      ]
    },
    {
      "name": "Plan",
      "entries": [
        {
          "text": "[Further evaluation of hypertension is needed, including a complete history and physical exam]",
          "source_indices": [
            1,
            87,
            79,
            167,
            251
          ]
        },
        {
          "text": "[Weight management counseling]",
          "source_indices": [
            80,
            168,
            252
          ]
        },
        {
          "text": "[Review of past medical records from previous physician (RDOG group) ]",
          "source_indices": [
            39,
            127,
            213
          ]
        }
      ]
    }
  ]
}
