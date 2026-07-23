from datetime import datetime, timezone
from sqlalchemy import select, update, insert
from .database import engine, resource_metadata_table

def get_resource_meta(resource_id):
    """Busca metadado armazenado."""
    with engine.connect() as conn:
        stmt = select(resource_metadata_table).where(
            resource_metadata_table.c.resource_id == resource_id
        )
        row = conn.execute(stmt).fetchone()
        return row._asdict() if row else None

def should_download(resource, stored_meta):
    """
    Decide se o recurso precisa ser baixado.
    Retorna (decisao, motivo) onde decisao é bool.
    """
    if stored_meta is None:
        return True, "NEW"
    # Comparar last_modified (API pode retornar string ISO)
    api_modified = resource.get("last_modified") or resource.get("revision_timestamp")
    stored_modified = stored_meta.get("last_modified_ckan")
    if api_modified and stored_modified:
        # Converter para datetime se necessário
        if isinstance(api_modified, str):
            api_modified = datetime.fromisoformat(api_modified.replace("Z", "+00:00"))
        if api_modified > stored_modified:
            return True, "UPDATED (modified date)"
    # Verificar tamanho
    api_size = resource.get("size")
    if api_size and stored_meta.get("size") and api_size != stored_meta["size"]:
        return True, "UPDATED (size change)"
    # Caso contrário, assumimos que não mudou
    return False, "UNCHANGED"

def upsert_metadata(resource, hash_value, status, processed_at=None):
    """Insere ou atualiza registro de metadados."""
    data = {
        "resource_id": resource["id"],
        "package_id": resource["package_id"],
        "resource_name": resource.get("name"),
        "url": resource.get("url"),
        "format": resource.get("format"),
        "last_modified_ckan": resource.get("last_modified") or resource.get("revision_timestamp"),
        "size": resource.get("size"),
        "content_hash": hash_value,
        "downloaded_at": datetime.now(timezone.utc),
        "processed_at": processed_at or datetime.now(timezone.utc),
        "status": status
    }
    with engine.begin() as conn:
        # Tentar update, se não existir insere
        stmt = update(resource_metadata_table).where(
            resource_metadata_table.c.resource_id == resource["id"]
        ).values(**data)
        result = conn.execute(stmt)
        if result.rowcount == 0:
            conn.execute(insert(resource_metadata_table).values(**data))