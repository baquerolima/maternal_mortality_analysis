import hashlib
import tempfile
import pandas as pd
import requests
from datetime import datetime, timezone
from sqlalchemy import Table, Column, String, DateTime, Text, MetaData
from .database import engine, metadata

# Criar tabela staging para SIM (exemplo, depois adapte para SINASC)
def get_staging_table(prefixo="stg_sim"):
    return Table(
        prefixo,
        metadata,
        Column("resource_id", String, index=True),
        Column("ingestion_ts", DateTime(timezone=True)),
        # Adicione colunas do CSV aqui; por enquanto usaremos uma coluna genérica 'dados_brutos'
        Column("linha_json", Text),   # armazena a linha inteira como JSON para posterior transformação
        schema="sus",
        keep_existing=True
    )

# Cria tabelas no banco se não existirem (executar na inicialização)
def criar_tabelas_staging():
    for nome in ["stg_sim", "stg_sinasc"]:
        tbl = get_staging_table(nome)
        if not engine.dialect.has_table(engine, tbl.name, schema="sus"):
            tbl.create(engine)

def download_and_hash(url):
    """Faz download do arquivo em tempfile, calcula SHA256 e retorna o caminho e o hash."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        sha = hashlib.sha256()
        for chunk in resp.iter_content(chunk_size=8192):
            tmp.write(chunk)
            sha.update(chunk)
        tmp_path = tmp.name
        hash_digest = sha.hexdigest()
    return tmp_path, hash_digest

def process_resource(resource, staging_table_name):
    """
    Baixa o CSV, confere hash e, se novo, carrega na staging.
    Retorna (status, hash) para atualização dos metadados.
    """
    url = resource["url"]
    tmp_path, file_hash = download_and_hash(url)
    try:
        # Ler CSV com pandas (aceita DBC? Não, mas vamos supor CSV)
        df = pd.read_csv(tmp_path, dtype=str, low_memory=False)
        df["resource_id"] = resource["id"]
        df["ingestion_ts"] = datetime.now(timezone.utc)
        # Converter cada linha para JSON (exemplo simples; no seu caso você mapeará colunas)
        df["linha_json"] = df.apply(lambda row: row.to_json(), axis=1)

        tbl = get_staging_table(staging_table_name)
        # Escrever no PostgreSQL (substituir ou deletar linhas antigas do mesmo resource_id)
        with engine.begin() as conn:
            # Remove registros anteriores deste recurso na staging
            conn.execute(tbl.delete().where(tbl.c.resource_id == resource["id"]))
            # Insere novos registros
            dados_para_inserir = df[["resource_id", "ingestion_ts", "linha_json"]].to_dict(orient="records")
            conn.execute(tbl.insert(), dados_para_inserir)

        return "UPDATED", file_hash
    finally:
        import os
        os.unlink(tmp_path)   # apaga arquivo temporário