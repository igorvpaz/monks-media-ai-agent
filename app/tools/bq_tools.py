"""
Ferramentas de BigQuery para o agente de análise de mídia e receita.

Clean Architecture: Cada ferramenta é responsável por uma área de domínio específica
(Tráfego vs Receita), com schemas Pydantic tipados e tratamento robusto de erros.
"""

import logging
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from google.cloud import bigquery

logger = logging.getLogger(__name__)


class VolumeTrafegoInput(BaseModel):
    """Input schema para consulta de volume de tráfego por canal."""

    canal: str = Field(
        default="",
        description="O canal de tráfego a ser filtrado (ex: 'Search', 'Organic', 'Facebook'). Se não especificado, retorna todos.",
    )
    meses_atras: int = Field(
        default=1,
        ge=1,
        le=12,
        description="Quantidade de meses para analisar no passado (1-12). Padrão: 1.",
    )


class ReceitaFaturamentoInput(BaseModel):
    """Input schema para consulta de receita e faturamento por canal."""

    canal: str = Field(
        default="",
        description="O canal de mídia para filtrar receita (ex: 'Search', 'Organic', 'Direct'). Se não especificado, retorna todos.",
    )
    meses_atras: int = Field(
        default=1,
        ge=1,
        le=12,
        description="Quantidade de meses para analisar (1-12). Padrão: 1.",
    )


@tool("consultar_volume_trafego", args_schema=VolumeTrafegoInput)
def consultar_volume_trafego(canal: str = "", meses_atras: int = 1) -> str:
    """
    Ferramenta 1: Consulta volume de usuários por canal de mídia.

    Use quando o usuário perguntar sobre: número de acessos, usuários adquiridos,
    volume de tráfego, performance de canais de atração.

    Retorna dados agregados de usuários agrupados por canal de tráfego.
    """
    try:
        client = bigquery.Client()

        query = """
            SELECT
                traffic_source as canal,
                COUNT(DISTINCT id) as total_usuarios,
                COUNT(id) as total_eventos
            FROM
                `bigquery-public-data.thelook_ecommerce.users`
            WHERE
                created_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL @meses_atras MONTH))
        """

        job_config_params = [
            bigquery.ScalarQueryParameter("meses_atras", "INT64", meses_atras)
        ]

        if canal.strip():
            query += " AND LOWER(traffic_source) = LOWER(@canal)"
            job_config_params.append(
                bigquery.ScalarQueryParameter("canal", "STRING", canal)
            )

        query += " GROUP BY traffic_source ORDER BY total_usuarios DESC"

        job_config = bigquery.QueryJobConfig(query_parameters=job_config_params)

        logger.info(
            f"Consultando volume de tráfego - Canal: {canal or 'todos'}, Meses: {meses_atras}"
        )
        resultados = client.query(query, job_config=job_config).result()
        linhas = [dict(row) for row in resultados]

        if not linhas:
            return (
                f"Nenhum dado de tráfego encontrado para o canal '{canal}' "
                f"nos últimos {meses_atras} mês(es)."
            )

        return str(linhas)

    except Exception as e:
        logger.error(f"Erro ao consultar volume de tráfego: {str(e)}")
        return f"❌ Erro ao consultar BigQuery: {str(e)}"


@tool("consultar_receita_faturamento", args_schema=ReceitaFaturamentoInput)
def consultar_receita_faturamento(canal: str = "", meses_atras: int = 1) -> str:
    """
    Ferramenta 2: Consulta receita total, AOV (Average Order Value) e análise de faturamento por canal.

    Use quando o usuário perguntar sobre: receita, faturamento, vendas, AOV,
    análise de conversão por canal, receita média por usuário.

    QUERY com JOINs: Combina dados de usuários (traffic_source) com orders e order_items.
    Usa funções de agregação: SUM (receita total), AVG (AOV), COUNT (num pedidos).
    """
    try:
        client = bigquery.Client()

        query = """
            SELECT
                u.traffic_source as canal_midia,
                COUNT(DISTINCT o.order_id) as total_pedidos,
                COUNT(DISTINCT u.id) as total_usuarios,
                SUM(oi.sale_price) as receita_total,
                ROUND(AVG(oi.sale_price), 2) as aov_medio,
                ROUND(SUM(oi.sale_price) / COUNT(DISTINCT u.id), 2) as receita_por_usuario,
                ROUND(COUNT(DISTINCT o.order_id) / COUNT(DISTINCT u.id), 3) as taxa_conversao_usuarios
            FROM
                `bigquery-public-data.thelook_ecommerce.users` u
            LEFT JOIN
                `bigquery-public-data.thelook_ecommerce.orders` o ON u.id = o.user_id
            LEFT JOIN
                `bigquery-public-data.thelook_ecommerce.order_items` oi ON o.order_id = oi.order_id
            WHERE
                u.created_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL @meses_atras MONTH))
                AND o.created_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL @meses_atras MONTH))
        """

        job_config_params = [
            bigquery.ScalarQueryParameter("meses_atras", "INT64", meses_atras)
        ]

        if canal.strip():
            query += " AND LOWER(u.traffic_source) = LOWER(@canal)"
            job_config_params.append(
                bigquery.ScalarQueryParameter("canal", "STRING", canal)
            )

        query += " GROUP BY u.traffic_source ORDER BY receita_total DESC"

        job_config = bigquery.QueryJobConfig(query_parameters=job_config_params)

        logger.info(
            f"Consultando receita/faturamento - Canal: {canal or 'todos'}, Meses: {meses_atras}"
        )
        resultados = client.query(query, job_config=job_config).result()
        linhas = [dict(row) for row in resultados]

        if not linhas:
            return (
                f"Nenhum dado de faturamento encontrado para o canal '{canal}' "
                f"nos últimos {meses_atras} mês(es)."
            )

        return str(linhas)

    except Exception as e:
        logger.error(f"Erro ao consultar receita/faturamento: {str(e)}")
        return f"❌ Erro ao consultar BigQuery: {str(e)}"


# Lista de todas as ferramentas disponíveis para o agente
TOOLS_DO_AGENTE = [consultar_volume_trafego, consultar_receita_faturamento]