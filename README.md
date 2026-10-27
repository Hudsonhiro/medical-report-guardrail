# Medical Report Guardrail 🛡️

Sistema de validação e sanitização de dados extraídos por LLMs para o setor de saúde, utilizando **Python** e contratos de dados estritos com **Pydantic v2**.

## 📌 O Problema
Modelos de Linguagem (LLMs) são sistemas probabilísticos suscetíveis a alucinações, formatos inconsistentes e falhas de tipagem. No ambiente médico, liberar relatórios com idades inválidas, registros profissionais inexistentes ou sem rastreabilidade de evidência gera riscos operacionais graves.

## 🚀 A Solução
Este projeto implementa uma barreira determinística (Guardrail) que:
- Valida integridade estrutural e tipos em tempo de execução via **Pydantic**.
- Impõe regras biológicas (como faixa de idade realista) através de `@field_validator`.
- Exige rastreabilidade obrigatória (`trecho_citado`) para combater respostas sem embasamento documental.
- Trata exceções de forma resiliente, impedindo que dados corrompidos cheguem a bancos de dados ou pipelines downstream.

## 🛠️ Tecnologias
- Python 3.11+
- Pydantic v2

## ⚙️ Como Executar
1. Instale as dependências:
   ```bash
   pip install -r requirements.txt