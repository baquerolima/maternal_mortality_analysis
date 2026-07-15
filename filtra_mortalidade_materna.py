import pandas as pd
import os
import glob

# Pasta contendo os arquivos CSV
pasta_sim = "arquivos/SIM"

# Lista todos os arquivos CSV, ordenados
arquivos = sorted(glob.glob(os.path.join(pasta_sim, "dados_*.csv")))

# Lista para armazenar os DataFrames filtrados
dfs_filtrados = []

for arquivo in arquivos:
    print(f"Processando: {arquivo}")
    
    # Lê o CSV com separador ponto-e-vírgula e encoding latin1
    df = pd.read_csv(arquivo, sep=";", encoding="latin1", dtype=str)
    
    # Normaliza os nomes das colunas para MAIÚSCULO
    df.columns = df.columns.str.upper()
    
    # Verifica se a coluna TPMORTEOCO existe
    if "TPMORTEOCO" not in df.columns:
        print(f"  ERRO: coluna TPMORTEOCO não encontrada em {arquivo}")
        continue
    
    # Filtra registros com TPMORTEOCO em {1, 2, 3, 4, 5}
    df_filtrado = df[df["TPMORTEOCO"].isin(["1", "2", "3", "4", "5"])]
    
    print(f"  Total registros: {len(df)} | Registros filtrados: {len(df_filtrado)}")
    
    if len(df_filtrado) > 0:
        dfs_filtrados.append(df_filtrado)

# Concatena todos os DataFrames filtrados
if dfs_filtrados:
    df_final = pd.concat(dfs_filtrados, ignore_index=True)
    print(f"\nTotal de registros filtrados (todos os anos): {len(df_final)}")
    
    # Salva o resultado
    df_final.to_csv("registros_mm.csv", sep=";", index=False, encoding="utf-8-sig")
    print("Arquivo registros_mm.csv salvo com sucesso!")
    print(f"Colunas: {list(df_final.columns)}")
else:
    print("Nenhum registro encontrado para os filtros aplicados.")