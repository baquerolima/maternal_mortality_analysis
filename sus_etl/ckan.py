import requests

CKAN_API = "https://opendatasus.saude.gov.br/api/3/action"

def search_resources(termo, rows=1000):
    """Retorna lista de recursos (dict) para o termo de busca."""
    params = {"q": termo, "rows": rows}
    url = f"{CKAN_API}/package_search"
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    packages = resp.json()["result"]["results"]
    resources = []
    for pkg in packages:
        for res in pkg.get("resources", []):
            res["package_id"] = pkg["id"]       # injeta package_id
            resources.append(res)
    return resources

def get_all_sus_resources():
    """Coleta recursos de SIM e SINASC."""
    sim = search_resources("sim")
    sinasc = search_resources("sinasc")
    return sim + sinasc