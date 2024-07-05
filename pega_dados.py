import pandas as pd
import json
import urllib3

def pega_urls(url_base):
    """
    Função que acessa a BASE_URL do SIM e do SINASC para pegar as url's dos arquivos anuais.
    """
    http = urllib3.PoolManager()
    u = http.request('GET', url_base, preload_content=False)
    j = json.loads(u.read())
    r = j['result']['results'][0]['resources']
    lista = []
    for item in r:
        lista.append((item['name'], item['url']))
        print(item['name'], item['url'])
    return lista

def gera_arquivo(url, name):
    """
    Função que acessa a URL indicada, lê o conteúdo e grava num arquivo .csv
    TODO:
    Essa é a função que precisa ser modificada para ler o conteúdo e já gravar num banco de dados.
    """
    http = urllib3.PoolManager()
    r = http.request('GET', url, preload_content=False)

    with open(name, 'wb') as out:
        while True:
            data = r.read()
            if not data:
                break
            out.write(data)


BASE_URL = 'http://opendatasus.saude.gov.br/api/3/action/package_search?q='

lista_sim = pega_urls(BASE_URL + 'SIM')
lista_sinasc = pega_urls(BASE_URL + 'SINASC')

for arquivo in lista_sim:
    print(arquivo[0], arquivo[1])
    gera_arquivo(url=arquivo[1], name=f"sim_{arquivo[0]}")

for arquivo in lista_sinasc:
    print(arquivo[0], arquivo[1])
    gera_arquivo(url=arquivo[1], name=f"sinasc_{arquivo[0]}")

