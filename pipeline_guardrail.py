import json
from typing import Optional
from google import genai
from pydantic import BaseModel, Field, ValidationError, field_validator


# 1. Strict clinical data contract
class MedicalReport(BaseModel):
    patient_name: str = Field(description="Full name of the patient")
    patient_age: int = Field(description="Patient age in integer years")
    diagnosis: str = Field(description="Identified medical diagnosis or clinical condition")
    prescription: Optional[str] = Field(
        default=None,
        description="Prescribed medication and dosage. If none is mentioned, return null. Do NOT invent data.",
    )
    attending_physician: str = Field(description="Full name of the physician in charge")
    medical_license: str = Field(description="State medical license number (CRM/UF)")
    cited_evidence: str = Field(
        description="Exact quote from the source text supporting the clinical finding"
    )

    @field_validator("patient_age")
    def validate_biological_age(cls, value: int):
        if value <= 0 or value > 125:
            raise ValueError(
                f"Age {value} is outside biological limits (must be between 1 and 125)."
            )
        return value

    @field_validator("medical_license")
    def validate_license_format(cls, value: str):
        cleaned_value = value.strip()
        if len(cleaned_value) < 4:
            raise ValueError(
                f"License '{value}' is invalid: must contain at least 4 characters."
            )
        return cleaned_value


# 2. Client initialization
client = genai.Client()


# 3. Guardrail sanitation barrier
def extract_and_validate_report(source_document: str) -> Optional[MedicalReport]:
    """
    Extracts clinical data using an LLM and validates the payload against strict business rules.
    Returns a validated MedicalReport instance or None if constraints fail.
    """
    print("\n--- INITIATING CLINICAL DOCUMENT EXTRACTION ---")

    prompt = (
        "You are a clinical extraction assistant. "
        "Extract the medical entities from the provided text according to the following rules:\n"
        "- If a field is missing, set its value to null.\n"
        "- Extract verbatim quotes for 'cited_evidence'.\n\n"
        f"Source document:\n{source_document}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": MedicalReport,
            },
        )
        raw_payload = json.loads(response.text)
    except Exception as api_err:
        print(f"[API ERROR] Failed to query LLM service: {api_err}")
        return None

    try:
        validated_report = MedicalReport(**raw_payload)
        print(" [PASSED] Report adheres to all clinical and schema constraints.")
        return validated_report
    except ValidationError as val_err:
        print(" [GUARDRAIL INTERCEPTED] Schema violation detected:")
        for error in val_err.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            print(f"   • Field '{field_path}': {error['msg']}")
        return None


# ==========================================
# TEST SUITE: PRODUCTION SCENARIOS
# ==========================================

if __name__ == "__main__":
    # Test 1: Valid admission report
    valid_record = """
    Patient Mariana Souza, 38 years old, admitted with a mild acute asthma attack.
    Prescription: Salbutamol inhaler 100mcg/dose as needed.
    Attending physician: Dr. Carlos Silva, CRM 54321-SP.
    """

    # Test 2: Impossible biological age (Data entry error or hallucination)
    invalid_age_record = """
    Patient Jose Albuquerque, 185 years old, presented with joint pain.
    Rest and observation advised.
    Attending physician: Dr. Helena Costa, CRM 99887-MG.
    """

    print(">>> RUNNING SCENARIO 1 (VALID RECORD)")
    report_1 = extract_and_validate_report(valid_record)
    if report_1:
        print(f"Patient admitted successfully: {report_1.patient_name}")
        print(f"Prescription recorded: {report_1.prescription}")

    print("\n>>> RUNNING SCENARIO 2 (BIOLOGICAL ANOMALY)")
    report_2 = extract_and_validate_report(invalid_age_record)
    if not report_2:
        print("Record safely routed to human audit queue.")