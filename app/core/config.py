"""
Configuração central da aplicação.
Carrega variáveis de ambiente a partir do arquivo .env usando pydantic-settings.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações da aplicação lidas do ambiente.

    Atributos:
        anthropic_api_key: Chave de API para o Claude (Anthropic).
        gcp_project_id: ID do projeto no Google Cloud Platform.
        google_application_credentials: Caminho para o arquivo JSON de credenciais do GCP.
        bigquery_dataset: Dataset padrão para consultas no BigQuery.
        app_name: Nome da aplicação (usado nos logs e metadados).
        app_version: Versão da aplicação.
        debug: Habilita o modo de depuração do FastAPI.
    """

    # Anthropic
    anthropic_api_key: str = ""

    # GCP / BigQuery
    gcp_project_id: str = ""
    google_application_credentials: str = ""
    bigquery_dataset: str = ""

    # App
    app_name: str = "Agente de Mídia IA"
    app_version: str = "0.1.0"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Retorna uma instância cacheada das configurações.
    O cache garante que o arquivo .env seja lido apenas uma vez.
    """
    return Settings()
