import pytest
from pydantic import ValidationError
from api import MedicalReport


def test_valid_medical_report():
    """Verify that a valid clinical payload passes all guardrails."""
    data = {
        "patient_name": "Mariana Souza",
        "patient_age": 38,
        "diagnosis": "Acute asthma attack",
        "prescription": "Salbutamol 100mcg",
        "attending_physician": "Dr. Carlos Silva",
        "medical_license": "54321-SP",
        "cited_evidence": "admitted with a mild acute asthma attack",
    }
    report = MedicalReport(**data)
    assert report.patient_name == "Mariana Souza"
    assert report.patient_age == 38


def test_missing_prescription_defaults_to_none():
    """Verify that missing prescriptions are safely handled as None without hallucination."""
    data = {
        "patient_name": "Lucas Pereira",
        "patient_age": 29,
        "diagnosis": "Post-infectious cough",
        "attending_physician": "Dr. Roberto Dias",
        "medical_license": "11223-MG",
        "cited_evidence": "Clinical suspicion of post-infectious cough",
    }
    report = MedicalReport(**data)
    assert report.prescription is None


def test_invalid_biological_age_raises_error():
    """Verify that impossible ages trigger a Pydantic ValidationError."""
    data = {
        "patient_name": "Jose Albuquerque",
        "patient_age": 185,
        "diagnosis": "Joint pain",
        "prescription": None,
        "attending_physician": "Dr. Helena Costa",
        "medical_license": "99887-MG",
        "cited_evidence": "presented with joint pain",
    }
    with pytest.raises(ValidationError) as exc_info:
        MedicalReport(**data)

    assert "violates biological constraints" in str(exc_info.value)


def test_short_medical_license_raises_error():
    """Verify that malformed CRM licenses under 4 characters are rejected."""
    data = {
        "patient_name": "Ana Lima",
        "patient_age": 45,
        "diagnosis": "Hypertension",
        "prescription": "Losartan 50mg",
        "attending_physician": "Dr. Marcos",
        "medical_license": "12",
        "cited_evidence": "diagnosed with hypertension",
    }
    with pytest.raises(ValidationError):
        MedicalReport(**data)