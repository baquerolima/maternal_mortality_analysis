import pandas as pd
import os


def lendo():
    sim = [reading_sim(a) for a in range(1996, 2024)]



def reading_sim(ano):
    colunas = ['CONTADOR', 'TIPOBITO', 'DTOBITO', 'NATURAL', 'DTNASC', 'IDADE', 'SEXO', 'RACACOR', 'ESTCIV', 'OCUP', 
               'CODMUNRES', 'LOCOCOR', 'CODMUNOCOR', 'IDADEMAE', 'OCUPMAE', 'QTDFILVIVO', 'QTDFILMORT', 'GRAVIDEZ', 
               'PARTO', 'OBITOPARTO', 'PESO', 'ASSISTMED', 'NECROPSIA', 'LINHAA', 'LINHAB', 'LINHAC', 'LINHAD', 'LINHAII', 
               'CIRCOBITO', 'ACIDTRAB', 'FONTE', 'ESC', 'ESCMAE', 'EXAME', 'CIRURGIA', 'OBITOGRAV', 'OBITOPUERP', 'CAUSABAS', 
               'GESTACAO' ]

    return pd.read_csv(f'dados_SIM/dados_{ano}.csv', sep=';', encoding='latin1', low_memory=False, usecols=colunas)


if __name__ == '__main__':
    lendo()