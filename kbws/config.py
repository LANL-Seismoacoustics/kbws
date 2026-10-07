from typing import Annotated, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load database configuration from a ".env" file
class Settings(BaseSettings):
    database_url: str
    log_level: Annotated[str, Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]]

    affiliation: str
    amplitude: str
    arrival: str
    assoc: str
    event: str
    gregion: str
    instrument: str
    lastid: str
    netmag: str
    network: str
    origerr: str
    origin: str
    remark: str
    sensor: str
    site: str
    sitechan: str
    sregion: str
    stamag: str
    wfdisc: str
    wftag: str

    model_config = SettingsConfigDict(
        env_file = ".env", # looks for a file named ".env" in the current working directory
        env_file_encoding = 'utf-8',
    )

settings = Settings()
