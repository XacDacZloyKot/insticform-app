import logging

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class RunSetting(BaseModel):
    port: int = 8000
    host: str = '0.0.0.0'
    debug: bool = True
    log_level: str = 'debug'
    reload: bool = True


class TokenSetting(BaseModel):
    secret_key: str = "149f0feb6cfbfcf801d16a2a2226a2a2bf2ba91c31f72527599ec543bd6bde7c9a2f589f15bf554ba84417abba577340b811be4b43adf6a84616e46054a1e3bb"
    access_token_expires_minutes: int = 720
    refresh_token_expires_minutes: int = 10080
    algorithm: str = "HS256"


class CORSSetting(BaseModel):
    allow_origin: list[str] = ['*']
    allow_credentials: bool = True
    allow_methods: list[str] = ["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"]
    allow_headers: list[str] = [
        "Content-Type",
        "Set-Cookie",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Authorization"
    ]


class LoggerSettings(BaseModel):
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level: int = logging.INFO


class DBSetting(BaseModel):
    url: str = "sqlite+aiosqlite:///./src/db/insticform.db"
    echo: bool = False

class Settings(BaseSettings):
    db: DBSetting = DBSetting()
    cors: CORSSetting = CORSSetting()
    token: TokenSetting = TokenSetting()
    logger: LoggerSettings = LoggerSettings()
    run: RunSetting = RunSetting()


settings = Settings()
