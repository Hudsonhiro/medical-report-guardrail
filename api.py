import json
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from google import genai
from pydantic import BaseModel, Field, ValidationError, field_validator

app = FastAPI(
    title="Medical Report Guardrail API",
    description="Production-grade AI extraction and validation service for clinical records.",
    version="1.0.0",
)


# 1. API Input and Output Schemas
class ExtractionRequest(BaseModel):
    document_text: str = Field(
        ...,
        description="Raw unstructured medical clinical note",
        min_length=10,
    )


class MedicalReport(BaseModel):
    patient_name: str = Field(description="Full name of the patient")
    patient_age: int = Field(description="Patient age in integer years")
    diagnosis: str = Field(description="Identified medical diagnosis or clinical condition")
    prescription: Optional[str] = Field(
        default=None,
        description="Prescribed medication and dosage. If none is mentioned, return null.",
    )
    attending_physician: str = Field(description="Full name of the physician in charge")
    medical_license: str = Field(description="State medical license number (CRM/UF)")
    cited_evidence: str = Field(
        description="Exact quote from the source text supporting the clinical finding"
    )

    @field_validator("patient_age")
    def validate_biological_age(cls, value: int):
        if value <= 0 or value > 125:
            raise ValueError(f"Age {value} violates biological constraints (1-125 years).")
        return value

    @field_validator("medical_license")
    def validate_license_format(cls, value: str):
        cleaned_value = value.strip()
        if len(cleaned_value) < 4:
            raise ValueError(f"License '{value}' must contain at least 4 characters.")
        return cleaned_value


# 2. Client Initialization (Lazy loading for testability)
def get_genai_client() -> genai.Client:
    return genai.Client(http_options={"api_version": "v1beta"})


# 3. API Endpoints
@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "healthy", "service": "medical-report-guardrail"}


@app.post(
    "/api/v1/extract-report",
    response_model=MedicalReport,
    status_code=status.HTTP_200_OK,
    tags=["Extraction"],
)
def extract_report(payload: ExtractionRequest):
    prompt = (
        "You are a clinical extraction assistant. "
        "Extract medical entities from the provided text following strict rules:\n"
        "- If a field is missing, set its value to null.\n"
        "- Extract verbatim quotes for 'cited_evidence'.\n\n"
        f"Source document:\n{payload.document_text}"
    )

    # Step 1: Call LLM
    try:
        client = get_genai_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": MedicalReport,
            },
        )
        raw_data = json.loads(response.text)
    except Exception as api_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Inference provider failure: {str(api_err)}",
        )

    # Step 2: Guardrail Validation
    try:
        validated_report = MedicalReport(**raw_data)
        return validated_report
    except ValidationError as val_err:
        error_details = [
            {"field": " -> ".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in val_err.errors()
        ]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Guardrail validation failed",
                "violations": error_details,
            },
        )