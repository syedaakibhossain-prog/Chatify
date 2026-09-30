from pydantic_settings import BaseSettings, SettingsConfigDict


class GlobalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ENVIRONMENT: str = "development"
    # app settings
    ALLOWED_ORIGINS: str = "http://127.0.0.1:3000,http://localhost:3000"

    DATABASE_URL: str ="sqlite+aiosqlite:///./database.db"

    # authentication related
    JWT_ACCESS_SECRET_KEY: str = "9d9bc4d77ac3a6fce1869ec8222729d2"
    JWT_REFRESH_SECRET_KEY: str = "fdc5635260b464a0b8e12835800c9016"
    ENCRYPTION_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    NEW_ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_enabled: bool = True
    trusted_proxy: bool = False
    
    SECONDS_TO_SEND_USER_STATUS: int = 60

   

    
    STATIC_HOST: str = "http://localhost:8001"




class DevelopmentSettings(GlobalSettings):
    pass


# class ProductionSettings(GlobalSettings):



def get_settings():

    return DevelopmentSettings()


settings = get_settings()



