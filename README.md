# **Projeto de ELT**
### Projeto desenvolvido como estudo durante a live do jornada de dados com o intuito de praticar os conhecimentos em extração, carregamento e transformação de dados de ponta a ponta.

<img src=img/img1.jpg width="100%">


## **1) Setup**
### **Local**
 - Definido o local de trabalho na pasta local
 - Configurado Github, Pyenv e ambiente virtual (Poetry)
 - Utilizado jupyter notebook para treino
 
 ### **Nuvem**
 - Criado ambiente free tier para storage utilizando supabase;
 - Upload das bases em parquet para o ambiente virtual.


## **2) Extração de dados**
- Criado conexão em python utilizando boto3 para simular conexão com DataLake AWS no SupaBase;
- Download dos arquivos Parquet utilizando looping for para automatizar;
- Conversão dos arquivos em DataFrames com Pandas.


## **3) Load**
- Carregamento dos arquivos no PostgreSQL utilizando looping for para automação. Dados ainda sem processamento.
