import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Numeric, Date, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Enums e Constantes
# Uso de STR e ENUM combinados para facilitar a serialização no Pydantic/FastAPI

class TipoLancamento(str, Enum):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"

class StatusTitulo(str, Enum):
    PENDENTE = "PENDENTE"
    PAGO = "PAGO"
    VENCIDO = "VENCIDO"
    CANCELADO = "CANCELADO"

# Configuração Base do ORM

class Base(DeclarativeBase):
    pass

# Tabelas Auxiliares e Cadastros Básicos

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255)) # Hash gerado via bcrypt/argon2
    data_criacao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Categoria(Base):
    # Categorização contábil por ex: alimentação, transporte, vendas
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), index=True)
    descricao: Mapped[Optional[str]] = mapped_column(String(200))
    
    # relacionamento reverso para queries
    titulos: Mapped[List["Titulo"]] = relationship(back_populates="categoria")

class Contato(Base):

    # unificação de clientes e fornecedores
    # evita duplicação de tabelas
    # uma entidade pode ser ambos.

    __tablename__ = "contatos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), index=True)
    documento: Mapped[Optional[str]] = mapped_column(String(20)) # CPF ou CNPJ sem formatação
    email: Mapped[Optional[str]] = mapped_column(String(100))
    telefone: Mapped[Optional[str]] = mapped_column(String(20))
    
    titulos: Mapped[List["Titulo"]] = relationship(back_populates="contato")

class ContaBancaria(Base):
    __tablename__ = "contas_bancarias"

    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(50))
    nome_banco: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Numeric(15,2) garante precisão para valores até trilhões 
    saldo_inicial: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    titulos: Mapped[List["Titulo"]] = relationship(back_populates="conta_bancaria")


# lançamentos financeiros

class Titulo(Base):

    # representa tanto contas a pagar quanto a receber
    # a diferenciação ocorre pelo campo 'tipo'
    
    __tablename__ = "titulos"

    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(255))
    
    # dados financeiros
    valor: Mapped[Decimal] = mapped_column(Numeric(15, 2)) 
    
    # controle de datas essencial para fluxo de caixa
    data_vencimento: Mapped[date] = mapped_column(Date, index=True)
    data_pagamento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # classificação
    tipo: Mapped[TipoLancamento] = mapped_column(String(10)) 
    status: Mapped[StatusTitulo] = mapped_column(String(10), default=StatusTitulo.PENDENTE, index=True)

    # lógica de parcelamento
    # 'id_transacao_pai' serve como correlation_id
    # se eu compro algo em 12x gero 12 registros aqui com o mesmo UUID neste campo.
    id_transacao_pai: Mapped[Optional[uuid.UUID]] = mapped_column(index=True, nullable=True)
    numero_parcela: Mapped[int] = mapped_column(default=1) 
    total_parcelas: Mapped[int] = mapped_column(default=1) 

    # Chaves Estrangeiras (FKs)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"))
    contato_id: Mapped[int] = mapped_column(ForeignKey("contatos.id"))
    conta_bancaria_id: Mapped[int] = mapped_column(ForeignKey("contas_bancarias.id"))

    # Relacionamentos (ORM)
    categoria: Mapped["Categoria"] = relationship(back_populates="titulos")
    contato: Mapped["Contato"] = relationship(back_populates="titulos")
    conta_bancaria: Mapped["ContaBancaria"] = relationship(back_populates="titulos")
    
    # Cascade delete: Se apagar o título, apaga os anexos do disco/banco
    anexos: Mapped[List["Anexo"]] = relationship(back_populates="titulo", cascade="all, delete-orphan")

class Anexo(Base):
    __tablename__ = "anexos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255)) # Nome original para download
    caminho_arquivo: Mapped[str] = mapped_column(String(500)) # Path relativo ou S3 Key
    data_upload: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    titulo_id: Mapped[int] = mapped_column(ForeignKey("titulos.id"))
    titulo: Mapped["Titulo"] = relationship(back_populates="anexos")