from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.seguranca import ALGORITMO, CHAVE_SECRETA
from app.modelo import Usuario
from app.schemas import TokenData


# Define que o token vem do header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def obter_usuario_logado(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    
    # decodifica o token JWT e busca o usuário no banco
    # se o token for falso ou expirado, barra a requisição aqui mesmo
    
    exception_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO])
        email: str = payload.get("sub")
        if email is None:
            raise exception_auth
        
        token_data = TokenData(email=email)
        
    except JWTError:
        raise exception_auth
    
    query = select(Usuario).where(Usuario.email == token_data.email)
    result = await db.execute(query)
    usuario = result.scalar_one_or_none()
    
    if usuario is None:
        raise exception_auth
        
    return usuario