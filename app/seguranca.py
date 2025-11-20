from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import jwt
import os

CHAVE_SECRETA = os.getenv("SECRET_KEY") 
if not CHAVE_SECRETA:
    raise ValueError("A variável de ambiente SECRET_KEY não foi configurada, verifique o .env")
ALGORITMO = "HS256"
MINUTOS_EXPIRACAO_TOKEN = 30

# configuração do Hashing Bcrypt
contexto_cripto = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_senha(senha_texto_puro: str, senha_hash: str) -> bool:
    # compara uma senha em texto plano com o hash do banco.
    return contexto_cripto.verify(senha_texto_puro, senha_hash)

def gerar_hash_senha(senha: str) -> str:
    # hash seguro da senha para salvar no banco.
    return contexto_cripto.hash(senha)

def criar_token_acesso(dados: dict, tempo_vida: Optional[timedelta] = None):
    # token JWT que o frontend vai usar para autenticar
    dados_para_codificar = dados.copy()
    
    if tempo_vida:
        expiracao = datetime.now(timezone.utc) + tempo_vida
    else:
        # usa o default de 30 min
        expiracao = datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_EXPIRACAO_TOKEN)
    
    # padrão JWT exige que a chave de expiração se chame 'exp'
    dados_para_codificar.update({"exp": expiracao})
    
    token_codificado = jwt.encode(dados_para_codificar, CHAVE_SECRETA, algorithm=ALGORITMO)
    return token_codificado