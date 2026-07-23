import logging
from datetime import datetime, timezone
from .ckan import get_all_sus_resources
from .metadata import get_resource_meta, should_download, upsert_metadata
from .processing import criar_tabelas_staging, process_resource
from .database import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    logging.info("Iniciando pipeline ETL semanal")
    criar_tabelas_staging()

    resources = get_all_sus_resources()
    logging.info(f"Encontrados {len(resources)} recursos (SIM + SINASC)")

    for res in resources:
        rid = res["id"]
        logging.info(f"Processando recurso {rid}: {res.get('name')}")
        stored = get_resource_meta(rid)
        download, reason = should_download(res, stored)
        if not download:
            logging.info(f"  -> Nenhuma alteração detectada ({reason})")
            # Atualiza campos de controle mesmo assim (opcional)
            upsert_metadata(res, stored["content_hash"] if stored else None, reason)
            continue

        logging.info(f"  -> Baixando e processando ({reason})")
        # Decide a tabela de staging com base no package ou nome (aqui simplificamos)
        nome = res.get("name", "").lower()
        if "sim" in nome:
            staging_tbl = "stg_sim"
        elif "sinasc" in nome or "nasc" in nome:
            staging_tbl = "stg_sinasc"
        else:
            staging_tbl = "stg_outros"

        try:
            status, file_hash = process_resource(res, staging_tbl)
            upsert_metadata(res, file_hash, status)
            logging.info(f"  -> Carga concluída com status: {status}")
        except Exception as e:
            logging.error(f"Falha ao processar {rid}: {e}", exc_info=True)

    logging.info("Pipeline finalizado. Execute as transformações para o star schema.")

if __name__ == "__main__":
    main()