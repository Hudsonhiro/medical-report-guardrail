import os
from google import genai
from pydantic import BaseModel, Field, field_validator

# 1. Contrato de dados estrito com Pydantic
class LaudoMedico(BaseModel):
    paciente_nome: str = Field(description="Nome completo do paciente")
    paciente_idade: int = Field(description="Idade do paciente em anos inteiros")
    diagnostico: str = Field(description="Diagnostico clinico identificado")
    prescricao: str = Field(description="Nome do medicamento e dosagem recomendada")
    medico_assinante: str = Field(description="Nome do medico responsavel")
    crm: str = Field(description="Numero do registro profissional CRM com UF")
    trecho_citado: str = Field(description="Citacao textual exata de onde o diagnostico foi extraido")

    @field_validator("paciente_idade")
    def validar_idade(cls, valor: int):
        if valor <= 0 or valor > 125:
            raise ValueError("Idade fora da faixa biológica válida (1 a 125 anos).")
        return valor

# 2. Inicializar o cliente da IA
cliente = genai.Client()

# 3. Texto livre e não estruturado de um atendimento
texto_atendimento = """
Paciente Mariana Souza, 38 anos, deu entrada na urgência relatando quadro agudo
de cefaleia unilateral pulsátil e náuseas intensas. Hipótese diagnóstica firmada:
crise de enxaqueca com aura.
Conduta: Sumatriptano 50mg via oral em dose única imediatamente.
Atendimento finalizado pela Dra. Camila Rocha, CRM 98765-RJ.
"""

print("Solicitando extração estruturada para a IA...")

# 4. Chamada da API forçando o schema do Pydantic
resposta = cliente.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"Extraia com precisão os dados clínicos deste atendimento:\n{texto_atendimento}",
    config={
        "response_mime_type": "application/json",
        "response_schema": LaudoMedico,
    },
)

# 5. O SDK já entrega o objeto tipado e validado pelo Pydantic
laudo_extraido: LaudoMedico = resposta.parsed

print("\n--- DADOS EXTRAÍDOS COM SUCESSO PELA IA ---")
print(f"Paciente: {laudo_extraido.paciente_nome}")
print(f"Idade: {laudo_extraido.paciente_idade} anos")
print(f"Diagnóstico: {laudo_extraido.diagnostico}")
print(f"Prescrição: {laudo_extraido.prescricao}")
print(f"Médico: {laudo_extraido.medico_assinante} | CRM: {laudo_extraido.crm}")
print(f"Evidência documental: \"{laudo_extraido.trecho_citado}\"")