import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.modelo import Base

# carrega a URL do banco de variáveis de ambiente
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("A variável DATABASE_URL não foi definida. Verifique o arquivo .env")

# gerencia o pool de conexões com o postgres
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    pool_size=10,      # Mantém até 10 conexões abertas
    max_overflow=20    # Permite estourar até 20 em picos de carga
)

# cria sessões de banco para cada requisição
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False # não desliga o objeto após o commit
)

# fastapi usa isso para entregar uma sessão limpa para cada endpoint
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            # o commit é feito manualmente na regra de negócio
        except Exception:
            await session.rollback() # rollback em caso de erro não tratado
            raise
        finally:
            await session.close() # devolve a conexão para o pool

# utilitário para criar tabelas usado apenas no startup/dev
async def init_db():
    async with engine.begin() as conn:
        # recria o schema baseado nos Models importados
        await conn.run_sync(Base.metadata.create_all)