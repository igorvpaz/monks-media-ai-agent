"""
Pydantic schemas for API request and response validation.
Inclui validações de segurança como limite de caracteres contra prompt injection.
"""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Schema para a requisição de consulta ao agente."""

    user_question: str = Field(
        ...,
        description="A pergunta ou instrução enviada pelo usuário ao agente.",
        examples=["Qual foi o volume de tráfego orgânico no último mês?"],
        min_length=1,
        max_length=500,
    )

    class Config:
        """Configurações de validação."""
        json_schema_extra = {
            "example": {
                "user_question": "Qual foi o volume de tráfego orgânico no último mês?"
            }
        }


class QueryResponse(BaseModel):
    """Schema para a resposta do agente."""

    agent_answer: str = Field(
        ...,
        description="A resposta gerada pelo agente de IA.",
        examples=["O volume de tráfego orgânico no último mês foi de 120.000 sessões."],
    )
