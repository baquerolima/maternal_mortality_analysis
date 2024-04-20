import pandas as pd
import json
from urllib import request as rq
import urllib3

def pega_arquivos(url):
    u = rq.urlopen(url)
    j = json.loads(u.read())
    r = j['result']['results'][0]['resources']
    lista = []
    for item in r:
        lista.append((item['name'], item['url']))
    return lista

def gera_arquivo(url, name):
    http = urllib3.PoolManager()
    r = http.request('GET', url, preload_content=False)

    with open(name, 'wb') as out:
        while True:
            data = r.read()
            if not data:
                break
            out.write(data)


BASE_URL = 'http://opendatasus.saude.gov.br/api/3/action/package_search?q='
sim = BASE_URL + 'SIM'
sinasc = BASE_URL + 'SINASC'

lista_sim = pega_arquivos(sim)
lista_sinasc = pega_arquivos(sinasc)

for arquivo in lista_sim:
    print(arquivo[0], arquivo[1])
    gera_arquivo(url=arquivo[1], name=f"sim_{arquivo[0]}")

for arquivo in lista_sinasc:
    print(arquivo[0], arquivo[1])
    gera_arquivo(url=arquivo[1], name=f"sinasc_{arquivo[0]}")

