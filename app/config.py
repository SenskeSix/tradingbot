from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    web_app_name: str = "tradingbot"
    env: str = "dev"

    # trading
    webhook_secret: str = Field(..., alias="WEBHOOK_SECRET")
    coinbase_api_key: str | None = Field(default=None, alias="COINBASE_API_KEY")
    coinbase_api_secret: str | None = Field(default=None, alias="COINBASE_API_SECRET")
    coinbase_api_passphrase: str | None = Field(default=None, alias="COINBASE_API_PASSPHRASE")
    trading_mode: str = Field("paper", alias="TRADING_MODE")
    base_assets: List[str] = Field(default_factory=lambda: ["BTC-USD"], alias="BASE_ASSETS")
    max_pos_pct: float = Field(0.25, alias="MAX_POS_PCT")
    max_daily_risk_pct: float = Field(0.5, alias="MAX_DAILY_RISK_PCT")
    order_slippage_pct: float = Field(0.1, alias="ORDER_SLIPPAGE_PCT")
    throttle_seconds: int = Field(30, alias="THROTTLE_SECONDS")
    paper_cash_usd: float = Field(100000, alias="PAPER_CASH_USD")

    # infrastructure
    db_url: str = Field(..., alias="DB_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    prometheus_port: int = Field(9000, alias="PROMETHEUS_PORT")
    internal_auth_token: str = Field(..., alias="INTERNAL_AUTH_TOKEN")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @field_validator("base_assets", mode="before")
    @classmethod
    def _split_assets(cls, value: List[str] | str) -> List[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
