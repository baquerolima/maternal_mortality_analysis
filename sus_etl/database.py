import os
from sqlalchemy import create_engine, MetaData, Table, Column, String, BigInteger, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)   # set echo=True para depuração local
metadata = MetaData(schema="sus")                  # usaremos schema "sus"

# Definição da tabela de metadados (criada fora do script, via migração inicial)
resource_metadata_table = Table(
    "resource_metadata",
    metadata,
    Column("resource_id", String, primary_key=True),
    Column("package_id", String, nullable=False),
    Column("resource_name", String),
    Column("url", String, nullable=False),
    Column("format", String),
    Column("last_modified_ckan", DateTime(timezone=True)),
    Column("size", BigInteger),
    Column("content_hash", String(64)),
    Column("downloaded_at", DateTime(timezone=True)),
    Column("processed_at", DateTime(timezone=True)),
    Column("status", String, default="NEW"),
    extend_existing=True
)