# Bibliotecas necessárias
import boto3
import pandas as pd
import io
from sqlalchemy import create_engine

# Configurações do DataLake
S3_ENDPOINT_URL = "xxxxx"
AWS_REGION = "us-west-2"
AWS_ACCESS_KEY_ID = "xxxxxf"
AWS_SECRET_ACCESS_KEY = "xxxx"
BUCKET_NAME = "meu_bucket"

# Criar cliente S3
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# Listar arquivos no bucket
response = s3.list_objects(Bucket=BUCKET_NAME)
arquivos = [obj["Key"] for obj in response["Contents"]]


# Lendo as 4 tabelas do DataLake (Parquet)

# Lista com os nomes das 4 tabelas que vamos carregar
TABELAS = ["produtos", "clientes", "vendas", "preco_competidores"]

# Dicionário vazio onde vamos guardar os DataFrames
# Chave = nome da tabela, Valor = DataFrame com os dados
dataframes = {}

# FOR 1: Percorrer cada tabela e baixar do DataLake
# Na 1ª volta: tabela = "produtos"
# Na 2ª volta: tabela = "clientes"
# Na 3ª volta: tabela = "vendas"
# Na 4ª volta: tabela = "preco_competidores"
for tabela in TABELAS:
    print(f"📥 Baixando {tabela}.parquet do DataLake...")

    # Montar o nome do arquivo: "produtos" → "produtos.parquet"
    file_key = f"{tabela}.parquet"

    # Baixar o arquivo do S3
    response = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
    parquet_bytes = response["Body"].read()

    # Converter bytes → DataFrame e guardar no dicionário
    dataframes[tabela] = pd.read_parquet(io.BytesIO(parquet_bytes))

    print(f"✅ {tabela}: {len(dataframes[tabela])} linhas carregadas")

# Resultado: dataframes = {
#   "produtos": DataFrame com dados de produtos,
#   "clientes": DataFrame com dados de clientes,
#   "vendas": DataFrame com dados de vendas,
#   "preco_competidores": DataFrame com dados de preços
# }


# Configurações do PostgreSQL (Supabase)
DATABASE_URL = "postgresql+psycopg2://xxxx"

# Criar engine de conexão
engine = create_engine(DATABASE_URL)

# FOR 2: Percorrer o dicionário e salvar cada tabela no banco
# .items() retorna pares (chave, valor) → (nome_tabela, dataframe)
# Na 1ª volta: tabela = "produtos", df = DataFrame de produtos
# Na 2ª volta: tabela = "clientes", df = DataFrame de clientes
# Na 3ª volta: tabela = "vendas", df = DataFrame de vendas
# Na 4ª volta: tabela = "preco_competidores", df = DataFrame de preços
for tabela, df in dataframes.items():
    print(f"💾 Salvando {tabela} no PostgreSQL...")

    df.to_sql(
        tabela,  # Nome da tabela no banco
        engine,  # Engine de conexão
        if_exists="replace",  # Substituir se existir
        index=False  # Não salvar índice do pandas
    )

    print(f"✅ {tabela}: {len(df)} linhas salvas no banco")

# FOR 3: Verificar se os dados foram salvos corretamente
# Agora lemos DO BANCO para confirmar que tudo chegou
print("\n📊 Verificação final:")
for tabela in TABELAS:
    df_verificacao = pd.read_sql_query(f"SELECT COUNT(*) as total FROM {tabela}", engine)
    total = df_verificacao["total"].iloc[0]
    print(f"  ✅ {tabela}: {total} linhas no banco")

# Fechar conexão
engine.dispose()

