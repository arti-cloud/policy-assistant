from pydantic import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str | None = None
    PINECONE_ENV: str | None = None
    VECTORSTORE_NAME: str = "company-policies"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_MODEL: str = "gpt-4o-mini"  # configurable
    MAX_CHUNKS: int = 8
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    ALLOW_INSECURE_LOCAL: bool = False
    # Auth / admin
    API_KEY: str | None = None  # a simple API key for backend endpoints
    PINECONE_USE: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
