import os
from typing import Optional
from google import genai
from pydantic import BaseModel, Field, field_validator

# 1. Contrato atualizado permitindo ausência estrita de dados
class LaudoMedico(BaseModel):
    paciente_nome: str = Field(description="Nome completo do paciente")
    paciente_idade: int = Field(description="Idade em anos inteiros")
    diagnostico: str = Field(description="Diagnóstico ou hipótese clínica identificada")
    
    # Campo opcional: deve ser None se não houver prescrição no texto
    prescricao: Optional[str] = Field(
        default=None,
        description="Nome do medicamento e dosagem. Se não houver medicamento prescrito no texto, retorne null. NÃO invente texto."
    )
    
    medico_assinante: str = Field(description="Nome do médico responsável")
    crm: str = Field(description="Registro profissional CRM com UF")
    trecho_citado: str = Field(description="Citação textual exata de onde o diagnóstico foi extraído")

    @field_validator("paciente_idade")
    def validar_idade(cls, valor: int):
        if valor <= 0 or valor > 125:
            raise ValueError("Idade fora da faixa biológica válida (1 a 125 anos).")
        return valor

# 2. Inicializar o cliente da IA
cliente = genai.Client()

# 3. Documento sem prescrição médica
texto_incompleto = """
Paciente Lucas Pereira, 29 anos, atendido no ambulatório relatando tosse seca 
persistente há 3 semanas. Ao exame físico: murmúrio vesicular universalmente audível, 
sem ruídos adventícios. Suspeita clínica de tosse pós-infecciosa. 
Paciente orientado a aguardar resultados de exames laboratoriais antes de iniciar conduta medicamentosa.
Atendimento conduzido pelo Dr. Roberto Dias, CRM 11223-MG.
"""

print("Solicitando extração de documento incompleto...")

resposta = cliente.models.generate_content(
    model="gemini-2.5-flash",
    contents=(
        "Extraia com precisão os dados clínicos deste atendimento. "
        "Atenção estrita: para qualquer informação que NÃO esteja descrita explicitamente no texto, preencha o campo correspondente com null.\n\n"
        f"Texto:\n{texto_incompleto}"
    ),
    config={
        "response_mime_type": "application/json",
        "response_schema": LaudoMedico,
    },
)

laudo_extraido: LaudoMedico = resposta.parsed

print("\n--- RESULTADO DA EXTRAÇÃO ESTRUTURADA ---")
print(f"Paciente: {laudo_extraido.paciente_nome}")
print(f"Idade: {laudo_extraido.paciente_idade} anos")
print(f"Diagnóstico: {laudo_extraido.diagnostico}")
print(f"Prescrição: {laudo_extraido.prescricao}")
print(f"Médico: {laudo_extraido.medico_assinante} | CRM: {laudo_extraido.crm}")
print(f"Evidência documental: \"{laudo_extraido.trecho_citado}\"")

# 4. Lógica de negócio downstream baseada em ausência segura
print("\n--- VALIDAÇÃO DE NEGÓCIO ---")
if laudo_extraido.prescricao is None:
    print(" Alerta: Atendimento sem conduta medicamentosa registrada. Nenhuma receita emitida.")
else:
    print(f" Receita gerada: {laudo_extraido.prescricao}")
    