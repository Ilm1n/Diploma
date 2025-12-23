from pathlib import Path

from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class RunConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000


class InvitationConfig(BaseModel):
    BASE_URL: str = "http://localhost:5173/invite"


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30


class S3Config(BaseModel):
    access_key: str
    secret_key: str
    bucket_name: str
    endpoint_url: str = "https://s3.ru1.storage.beget.cloud"
    region_name: str = "ru1"


class Files(BaseModel):
    avatar_max_size: int = 5 * 1024 * 1024  # 5 MB
    avatar_allowed_types: list[str] = ["image/jpeg", "image/png", "image/webp"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env.template", BASE_DIR / ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="LIGHTTASK_CONFIG__",
        extra="ignore",
    )
    run: RunConfig = RunConfig()
    db: DatabaseConfig
    auth_jwt: AuthJWT = AuthJWT()
    invite: InvitationConfig = InvitationConfig()
    s3: S3Config
    files: Files = Files()


settings = Settings()
