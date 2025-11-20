from pydantic import BaseModel, EmailStr, Field, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List
from app.modelo import TipoLancamento, StatusTitulo

class TokenData(BaseModel):
    # Schema usado para validar o payload do JWT.
    email: Optional[str] = None

class UsuarioBase(BaseModel):
    # EmailStr garante que o input é um formato de email válido.
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    # A senha é recebida aqui e transformada em hash no Backend.
    senha: str

class UsuarioResponse(UsuarioBase):
    # Retorno: NUNCA inclui o campo 'senha' ou 'senha_hash'.
    id: int
    data_criacao: datetime
    # ConfigDict(from_attributes=True) habilita a leitura de objetos SQLAlchemy (antigo orm_mode=True).
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class CategoriaBase(BaseModel):
    nome: str
    descricao: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ContatoBase(BaseModel):
    nome: str
    documento: Optional[str] = None
    # emailStr aqui garante formato válido para PII (informação pessoal).
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None

class ContatoCreate(ContatoBase):
    pass

class ContatoResponse(ContatoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TituloBase(BaseModel):
    descricao: str
    # validação Crítica: 'gt=0' garante que o valor é positivo
    valor: Decimal = Field(..., gt=0, description="Valor monetário positivo")
    
    data_vencimento: date
    tipo: TipoLancamento
    
    # validação Crítica: Field(..., gt=0) impede que IDs negativos ou zero sejam enviados
    categoria_id: int = Field(..., gt=0, description="ID válido da categoria")
    contato_id: int = Field(..., gt=0, description="ID válido do contato")
    conta_bancaria_id: int = Field(..., gt=0, description="ID válido da conta bancária")

class TituloCreate(TituloBase):
    parcelado: bool = False
    # validação: 'ge=1' (Greater than or Equal to 1) impede divisão por zero na lógica de parcelamento.
    total_parcelas: int = Field(1, ge=1, description="Número de parcelas (mínimo 1)")

class TituloResponse(TituloBase):
    id: int
    status: StatusTitulo
    numero_parcela: int
    total_parcelas: int
    data_criacao: datetime
    #configDict(from_attributes=True) para ler o retorno do banco
    model_config = ConfigDict(from_attributes=True)