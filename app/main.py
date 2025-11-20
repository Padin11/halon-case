from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.rotas import router 

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(" [Startup] inicializando sistema financeiro")
    try:
        await init_db()
        print(" [Database] tabelas verificadas/criadas com sucesso.")
    except Exception as e:
        print(f" [Erro Crítico] Falha ao conectar no banco: {e}")
    
    yield 
    print("desligando sistema financeiro")

# Definição da API
app = FastAPI(
    title="Sistema de Controle Financeiro - Case Técnico",
    description="API RESTful para gestão de fluxo de caixa, contas a pagar/receber e relatórios.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuração do CORS
origins = [
    "http://localhost",
    "http://localhost:3000", # React/Next.js padrão
    "http://localhost:5173", # Vite/Vue padrão
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],   
    allow_headers=["*"],   
)

app.include_router(router)

# ver se está tudo ok
@app.get("/health", tags=["Monitoramento"])
async def health_check():
    return {
        "status": "active",
        "servico": "financeiro-api",
        "versao": "1.0.0"
    }