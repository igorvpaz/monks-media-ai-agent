"""
Agente de IA Anthropic Claude para análise de mídia e faturamento.

Architecture:
- Separação clara entre: (1) lógica de prompt (app/core/prompts.py)
  (2) lógica de execução (agent_fresh.py) (3) ferramentas (app/tools/bq_tools.py)
- Tool use robusto com tratamento de erros específicos por camada
- Logging detalhado para debugging e auditoria
"""

import logging
import os
from anthropic import Anthropic

logger = logging.getLogger(__name__)


def consultar_agente_fresh(pergunta: str) -> str:
    """
    Executa o agente Anthropic Claude com imports frescos para cada requisição.

    Args:
        pergunta: Pergunta do usuário (já validada em schemas.py com max 500 chars)

    Returns:
        Resposta do agente em texto natural

    Raises:
        ValueError: Se ANTHROPIC_API_KEY estiver inválida
        anthropic.APIError: Se houver erro na API Anthropic
    """
    from dotenv import load_dotenv
    from app.core.prompts import SYSTEM_PROMPT_AGENT
    from app.tools.bq_tools import TOOLS_DO_AGENTE

    load_dotenv()

    # Validação: API Key obrigatória
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "Variável de ambiente ANTHROPIC_API_KEY não configurada. "
            "Adicione no arquivo .env"
        )
    if not api_key.startswith("sk-ant-"):
        raise ValueError(
            "ANTHROPIC_API_KEY não segue o formato esperado (sk-ant-...)"
        )

    logger.info(f"Iniciando agente | Pergunta: '{pergunta[:60]}...'")

    # Inicializa cliente Anthropic
    client = Anthropic(api_key=api_key)
    ferramentas_map = {t.name: t for t in TOOLS_DO_AGENTE}

    # Converte schemas Pydantic das ferramentas para formato Anthropic
    ferramentas_anthropic = []
    for tool in TOOLS_DO_AGENTE:
        schema = (
            tool.args_schema.model_json_schema()
            if hasattr(tool, "args_schema") and tool.args_schema
            else {"type": "object", "properties": {}, "required": []}
        )

        ferramentas_anthropic.append(
            {
                "name": tool.name,
                "description": tool.description or "Ferramenta disponível",
                "input_schema": schema,
            }
        )

    logger.debug(f"Ferramentas disponíveis: {[t['name'] for t in ferramentas_anthropic]}")

    mensagens = [{"role": "user", "content": pergunta}]

    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        try:
            logger.debug(f"Iteração {iteration}: Chamando Claude Haiku 4.5")

            # Chama Claude com as ferramentas bindadas
            resposta = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                system=SYSTEM_PROMPT_AGENT,
                tools=ferramentas_anthropic,
                messages=mensagens,
            )

            logger.debug(f"Iteração {iteration}: stop_reason={resposta.stop_reason}")

            # Caso 1: Modelo respondeu e finalizou (end_turn)
            if resposta.stop_reason == "end_turn":
                for bloco in resposta.content:
                    if hasattr(bloco, "text") and bloco.text:
                        logger.info("Agente finalizou com sucesso")
                        return bloco.text
                return "❌ Agente não gerou resposta"

            # Caso 2: Modelo quer usar ferramentas (tool_use)
            if resposta.stop_reason == "tool_use":
                mensagens.append({"role": "assistant", "content": resposta.content})

                # Executa ferramentas solicitadas pelo modelo
                resultados_tools = []
                for bloco in resposta.content:
                    if bloco.type == "tool_use":
                        nome_ferramenta = bloco.name
                        logger.debug(f"Executando ferramenta: {nome_ferramenta}")

                        ferramenta = ferramentas_map.get(nome_ferramenta)
                        if not ferramenta:
                            resultado_str = (
                                f"❌ Ferramenta '{nome_ferramenta}' não encontrada"
                            )
                            logger.error(resultado_str)
                        else:
                            try:
                                # Executa a ferramenta (BigQuery, etc)
                                resultado = ferramenta.invoke(bloco.input)
                                resultado_str = str(resultado)
                                logger.debug(
                                    f"Ferramenta {nome_ferramenta} executada com sucesso"
                                )
                            except Exception as e:
                                resultado_str = f"❌ Erro ao executar {nome_ferramenta}: {str(e)}"
                                logger.error(resultado_str, exc_info=True)

                        resultados_tools.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": bloco.id,
                                "content": resultado_str,
                            }
                        )

                mensagens.append({"role": "user", "content": resultados_tools})

            else:
                # Caso 3: Stop reason inesperado
                logger.warning(
                    f"Stop reason inesperado na iteração {iteration}: {resposta.stop_reason}"
                )
                for bloco in resposta.content:
                    if hasattr(bloco, "text") and bloco.text:
                        return bloco.text
                return f"⚠️  Resposta inesperada (stop_reason: {resposta.stop_reason})"

        except ValueError as e:
            # Erro de validação (API key inválida, etc)
            logger.error(f"Erro de validação na iteração {iteration}: {str(e)}")
            raise
        except Exception as e:
            # Erro genérico (falha na API, timeout, etc)
            logger.error(f"Erro na iteração {iteration}: {str(e)}", exc_info=True)
            raise

    logger.warning("Limite máximo de iterações atingido")
    return "⚠️  Limite de iterações atingido. Tente uma pergunta mais específica."
