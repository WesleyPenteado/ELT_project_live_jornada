# **Projeto de ELT**
### Projeto desenvolvido como estudo durante a live do jornada de dados com o intuito de praticar os conhecimentos em extração, carregamento e transformação de dados de ponta a ponta.

*Link do projeto original: https://github.com/lvgalvao/data-engineering-roadmap/tree/main/00-imersao-jornada*

<img src=img/img1.jpg width="100%">


## **1) Setup**
### **Local**
 - Definido o local de trabalho na pasta local
 - Configurado Github, Pyenv e ambiente virtual (Poetry)
 
 ### **Cloud**
 - Criado ambiente free tier para storage utilizando supabase;
 - Upload das bases em parquet para o storage do Supabase.


## **2) Extração de dados**
- Criado conexão em python utilizando boto3 para simular conexão com DataLake AWS, porém utilizando SupaBase;
- Download dos arquivos Parquet utilizando looping for para automatizar;
- Conversão dos arquivos em DataFrames com Pandas.


## **3) Load**
- Carregamento dos arquivos no PostgreSQL utilizando looping for para automação. Dados carregados no PostreSQL ainda sem transformações.


## **4) Transformation utilizando PRD + DBT + copilot agent**
- Utilizado arquitetura medalhão para manter a qualidade dos dados disponibilizados;
- Aplicado conceito de DATA MART atendendo as necessidades específicas das áreas de pricing, sales e customer success.
