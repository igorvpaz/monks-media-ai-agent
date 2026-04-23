"""
Endpoints da API REST para o Agente de Análise de Mídia e Receita.

Responsabilidades:
1. Validação de entrada (Pydantic schemas com proteção contra prompt injection)
2. Roteamento de requisições para o agente
3. Tratamento específico de erros por camada
4. Logging e auditoria
"""

import logging
from anthropic import APIError as AnthropicAPIError
from google.cloud.exceptions import GoogleCloudError
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.models.schemas import QueryRequest, QueryResponse
from app.agent.agent_fresh import consultar_agente_fresh

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post(
    "/ask",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Consulta ao agente de análise de mídia",
    description=(
        "Endpoint principal para fazer perguntas ao agente de IA. "
        "O agente consulta BigQuery para análise de tráfego e faturamento."
    ),
)
async def ask_agent(request: QueryRequest) -> QueryResponse:
    """
    Processa pergunta do usuário e retorna análise do agente.

    Validações implementadas:
    - max_length=500 chars na pergunta (prevenção contra prompt injection)
    - Tratamento específico para erros de: Anthropic API, BigQuery, validação

    Args:
        request: Pergunta validada pelo Pydantic (schemas.QueryRequest)

    Returns:
        QueryResponse com resposta do agente

    Raises:
        HTTPException 400: Validação falhou (msg muito longa, etc)
        HTTPException 401/403: Credenciais inválidas
        HTTPException 500: Erro no BigQuery ou API Anthropic
    """
    pergunta = request.user_question.strip()
    logger.info(f"Nova pergunta recebida ({len(pergunta)} chars): '{pergunta[:60]}...'")

    try:
        # Dispara o agente (imports frescos a cada requisição)
        resposta_agente = consultar_agente_fresh(pergunta)
        logger.info("✅ Resposta gerada com sucesso")
        return QueryResponse(agent_answer=resposta_agente)

    except ValueError as e:
        # Erro de configuração: ANTHROPIC_API_KEY inválida
        logger.error(f"❌ Erro de configuração: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Erro de autenticação: Credenciais da Anthropic não configuradas corretamente. "
                "Contate o administrador."
            ),
        ) from e

    except AnthropicAPIError as e:
        # Erro na API Anthropic: quota excedida, rate limit, etc
        logger.error(f"❌ Erro na API Anthropic: {str(e)}", exc_info=True)
        detail = "Erro ao comunicar com o serviço de IA. Tente novamente em alguns segundos."
        if "rate_limit" in str(e).lower():
            detail = (
                "Limite de requisições atingido. Aguarde um momento e tente novamente."
            )
        elif "quota" in str(e).lower():
            detail = "Quota de API excedida. Contate o administrador."

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        ) from e

    except GoogleCloudError as e:
        # Erro no BigQuery: conexão, permissões, query inválida, etc
        logger.error(f"❌ Erro no BigQuery: {str(e)}", exc_info=True)
        detail = "Erro ao consultar banco de dados. Tente novamente."
        if "not found" in str(e).lower():
            detail = "Tabela ou dataset do BigQuery não encontrado."
        elif "permission" in str(e).lower():
            detail = "Erro de permissão ao acessar BigQuery."

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        ) from e

    except ValidationError as e:
        # Erro na validação Pydantic (não deve acontecer aqui pois já passou em /ask)
        logger.error(f"❌ Erro de validação: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao validar entrada: {str(e)}",
        ) from e

    except Exception as e:
        # Erro genérico/inesperado
        logger.error(
            f"❌ Erro inesperado ao processar pergunta: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Erro interno ao processar sua solicitação. "
                "Tente novamente ou contate o suporte."
            ),
        ) from e