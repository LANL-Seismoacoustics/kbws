from typing import Annotated, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# Load database configuration from a ".env" file
class Settings(BaseSettings):
    database_url: str
    log_level: Annotated[str, Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]]
    logging_config: str = "logging.dev.ini"
    openapi_docs_header: str | None = None
    oracle_client_lib_dir: str | None = None
    # logging_config: str = "logging.server.ini"

    # amplitude: str | None = None  # unused by current KBWS services
    # gregion: str | None = None  # unused by current KBWS services
    # origerr: str | None = None  # unused by current KBWS services
    # remark: str | None = None  # unused by current KBWS services
    # sregion: str | None = None  # unused by current KBWS services
    # stamag: str | None = None  # unused by current KBWS services
    # wftag: str | None = None  # unused by current KBWS services

    affiliation: str | None = None
    arrival: str | None = None
    assoc: str | None = None
    event: str | None = None
    instrument: str | None = None
    netmag: str | None = None
    network: str | None = None
    origin: str | None = None
    sensor: str | None = None
    site: str | None = None
    sitechan: str | None = None
    wfdisc: str | None = None

    model_config = SettingsConfigDict(
        env_file = ".env", # looks for a file named ".env" in the current working directory
        env_file_encoding = 'utf-8',
    )

settings = Settings()
