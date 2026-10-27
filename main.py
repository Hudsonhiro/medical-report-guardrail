from pydantic import BaseModel, Field, field_validator
from typing import Optional

class LaudoMedicoGuardrail(BaseModel):
    paciente_nome: str = Field(description="Nome completo do paciente")
    paciente_idade: int = Field(description="Idade em anos inteiros")
    diagnostico: str = Field(description="Diagnóstico identificado")
    prescricao: str = Field(description="Medicamento e dosagem")
    medico_assinante: str = Field(description="Nome do médico responsável")
    crm: str = Field(description="Registro profissional do médico")
    trecho_citado: str = Field(description="Citação exata do documento original que comprova o laudo")

    @field_validator("paciente_idade")
    def validar_idade(cls, valor: int):
        if valor <= 0 or valor > 125:
            raise ValueError("Idade fora da faixa biológica válida (deve ser entre 1 e 125 anos).")
        return valor

    @field_validator("crm")
    def validar_crm(cls, valor: str):
        valor_limpo = valor.strip()
        if len(valor_limpo) < 4:
            raise ValueError("CRM inválido: o registro médico deve ter pelo menos 4 dígitos.")
        return valor_limpo


def processar_laudo_seguro(dados_brutos: dict) -> Optional[LaudoMedicoGuardrail]:
    """
    Função que atua como barreira sanitária (Guardrail).
    Recebe os dados crus gerados pela LLM e só devolve o objeto se for 100% válido.
    """
    try:
        laudo_validado = LaudoMedicoGuardrail(**dados_brutos)
        print(" [APROVADO] Laudo passou em todas as regras de conformidade!")
        return laudo_validado
    except Exception as erro:
        print(" [REJEITADO] Falha na validação do laudo:")
        print(f"Detalhes técnicos do erro:\n{erro}\n")
        return None


# ==========================================
# SIMULAÇÃO DE CENÁRIOS DE PRODUÇÃO
# ==========================================

print("=== Cenário 1: Extração perfeita com evidência ===")
payload_correto = {
    "paciente_nome": "Carlos Drummond",
    "paciente_idade": 52,
    "diagnostico": "Asma brônquica crônica",
    "prescricao": "Salbutamol 100mcg spray",
    "medico_assinante": "Dra. Beatriz Mendes",
    "crm": "45981-SP",
    "trecho_citado": "Paciente relata episódios recorrentes de dispneia noturna e sibilos."
}
laudo_aprovado = processar_laudo_seguro(payload_correto)
if laudo_aprovado:
    print(f"Paciente pronto para o banco de dados: {laudo_aprovado.paciente_nome}\n")

print("=== Cenário 2: Erro biológico de idade (IA alucinou ou erro de digitação) ===")
payload_idade_invalida = {
    "paciente_nome": "Carlos Drummond",
    "paciente_idade": -8,  # Idade absurda
    "diagnostico": "Asma brônquica",
    "prescricao": "Salbutamol",
    "medico_assinante": "Dra. Beatriz Mendes",
    "crm": "45981-SP",
    "trecho_citado": "Texto qualquer"
}
processar_laudo_seguro(payload_idade_invalida)

print("=== Cenário 3: CRM sem conformidade ===")
payload_crm_invalido = {
    "paciente_nome": "Carlos Drummond",
    "paciente_idade": 52,
    "diagnostico": "Asma brônquica",
    "prescricao": "Salbutamol",
    "medico_assinante": "Dra. Beatriz Mendes",
    "crm": "1",  # Menor que 4 caracteres
    "trecho_citado": "Texto qualquer"
}
processar_laudo_seguro(payload_crm_invalido)