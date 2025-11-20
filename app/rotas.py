from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case 
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.modelo import Usuario, Titulo, Categoria, Contato, ContaBancaria
from app.schemas import (
    UsuarioCreate, UsuarioResponse, Token, 
    TituloCreate, TituloResponse
)
from app import seguranca, deps, servicos
from app.schemas import CategoriaResponse

router = APIRouter()

@router.post("/auth/registro", response_model=UsuarioResponse, status_code=201)
async def registrar_usuario(usuario: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    # Verifica se email já existe
    query = select(Usuario).where(Usuario.email == usuario.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado.")
    
    # Cria usuário com senha hash
    novo_usuario = Usuario(
        email=usuario.email, 
        senha_hash=seguranca.gerar_hash_senha(usuario.senha)
    )
    db.add(novo_usuario)
    await db.commit()
    await db.refresh(novo_usuario)
    return novo_usuario

@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    # Busca usuário
    query = select(Usuario).where(Usuario.email == form_data.username)
    result = await db.execute(query)
    usuario = result.scalar_one_or_none()
    
    if not usuario or not seguranca.verificar_senha(form_data.password, usuario.senha_hash):
        raise HTTPException(status_code=400, detail="Email ou senha incorretos")
    
    token_acesso = seguranca.criar_token_acesso(dados={"sub": usuario.email})
    return {"access_token": token_acesso, "token_type": "bearer"}


@router.post("/titulos", response_model=List[TituloResponse], status_code=201)
async def criar_titulo(
    dados: TituloCreate,
    db: AsyncSession = Depends(get_db),
    usuario_atual: Usuario = Depends(deps.obter_usuario_logado)
):
    
    #Cria um ou múltiplos títulos (se for parcelado).
    novos_titulos = servicos.criar_titulos_parcelados(dados)
    
    db.add_all(novos_titulos)
    await db.commit()
    
    for t in novos_titulos:
        await db.refresh(t)
        
    return novos_titulos

@router.get("/titulos", response_model=List[TituloResponse])
async def listar_titulos(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    usuario_atual: Usuario = Depends(deps.obter_usuario_logado)
):
    query = select(Titulo).offset(skip).limit(limit).order_by(Titulo.data_vencimento)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/dashboard/resumo")
async def obter_resumo_financeiro(
    db: AsyncSession = Depends(get_db),
    usuario_atual: Usuario = Depends(deps.obter_usuario_logado)
):
   
    query = select(
        # 1. Saldo Líquido (Tudo que entrou - Tudo que saiu, independente do status)
        # (Ou ajustamos para ser apenas PAGOS se quiser fluxo de caixa realizado)
        func.sum(case((Titulo.tipo == "RECEITA", Titulo.valor), else_=0)) -
        func.sum(case((Titulo.tipo == "DESPESA", Titulo.valor), else_=0)),
        
        # 2. A Receber (Apenas Pendentes)
        func.sum(case((
            (Titulo.tipo == "RECEITA") & (Titulo.status == "PENDENTE"), 
            Titulo.valor
        ), else_=0)),
        
        # 3. A Pagar (Apenas Pendentes)
        func.sum(case((
            (Titulo.tipo == "DESPESA") & (Titulo.status == "PENDENTE"), 
            Titulo.valor
        ), else_=0)),
        
        # 4. Total Vencido (Crítico - Risco Financeiro)
        func.sum(case((Titulo.status == "VENCIDO", Titulo.valor), else_=0))
    )
    
    result = await db.execute(query)
    saldo, a_receber, a_pagar, vencido = result.one()
    
    # Tratamento de Nulos (Se o banco estiver vazio, retorna 0.00)
    return {
        "saldo_geral": saldo or 0,
        "total_a_receber": a_receber or 0,
        "total_a_pagar": a_pagar or 0,
        "total_inadimplente": vencido or 0
    }

@router.get("/dashboard/por-categoria")
async def obter_totais_por_categoria(
    db: AsyncSession = Depends(get_db),
    usuario_atual: Usuario = Depends(deps.obter_usuario_logado)
):
    
    #Dados para Gráfico de Rosca.
    #Mostra onde o dinheiro está indo (Top Despesas/Receitas).
    
    query = (
        select(Categoria.nome, func.sum(Titulo.valor))
        .join(Titulo.categoria)
        .group_by(Categoria.nome)
        .order_by(func.sum(Titulo.valor).desc()) # Ordena do maior para o menor
    )
    
    result = await db.execute(query)
    dados = result.all()
    
    return [{"categoria": nome, "total": valor} for nome, valor in dados]

@router.get("/dashboard/fluxo-caixa")
async def obter_fluxo_caixa_mensal(
    db: AsyncSession = Depends(get_db),
    usuario_atual: Usuario = Depends(deps.obter_usuario_logado)
):
  
    # Extrai o 'YYYY-MM' da data no Postgres
    mes_ano = func.to_char(Titulo.data_vencimento, 'YYYY-MM')
    
    query = (
        select(
            mes_ano.label("mes"),
            Titulo.tipo,
            func.sum(Titulo.valor)
        )
        .group_by(mes_ano, Titulo.tipo)
        .order_by(mes_ano)
    )
    
    result = await db.execute(query)
    dados = result.all()
    
    # Transforma a lista plana do SQL em um objeto estruturado para o Front
    # De: [('2025-01', 'RECEITA', 100), ('2025-01', 'DESPESA', 50)]
    # Para: {'2025-01': {'receitas': 100, 'despesas': 50}}
    relatorio = {}
    for mes, tipo, valor in dados:
        if mes not in relatorio:
            relatorio[mes] = {"mes": mes, "receitas": 0, "despesas": 0}
        
        if tipo == "RECEITA":
            relatorio[mes]["receitas"] = valor
        else:
            relatorio[mes]["despesas"] = valor
            
    return list(relatorio.values())

@router.get("/dashboard/ranking")
async def obter_ranking_contatos(
    db: AsyncSession = Depends(get_db),
    usuario_atual: Usuario = Depends(deps.obter_usuario_logado)
):
   
    # 1. Top Devedores (Quem nos deve)
    query_devedores = (
        select(Contato.nome, func.sum(Titulo.valor))
        .join(Titulo.contato)
        .where(Titulo.tipo == "RECEITA")
        .where(Titulo.status.in_(["PENDENTE", "VENCIDO"]))
        .group_by(Contato.nome)
        .order_by(func.sum(Titulo.valor).desc())
        .limit(5) # Top 5
    )
    
    # 2. Top Credores (Quem nós devemos)
    query_credores = (
        select(Contato.nome, func.sum(Titulo.valor))
        .join(Titulo.contato)
        .where(Titulo.tipo == "DESPESA")
        .where(Titulo.status.in_(["PENDENTE", "VENCIDO"]))
        .group_by(Contato.nome)
        .order_by(func.sum(Titulo.valor).desc())
        .limit(5) # Top 5
    )
    
    res_devedores = await db.execute(query_devedores)
    res_credores = await db.execute(query_credores)
    
    return {
        "devedores": [{"nome": nome, "total": valor} for nome, valor in res_devedores.all()],
        "credores": [{"nome": nome, "total": valor} for nome, valor in res_credores.all()]
    }

@router.get("/categorias", response_model=List[CategoriaResponse])
async def listar_categorias(
    db: AsyncSession = Depends(get_db),
    usuario_atual: Usuario = Depends(deps.obter_usuario_logado)
):
    query = select(Categoria).order_by(Categoria.nome)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/dashboard/busca-contato")
async def buscar_financeiro_contato(
    q: str, # Query param: ?q=Nome
    db: AsyncSession = Depends(get_db),
    usuario_atual: Usuario = Depends(deps.obter_usuario_logado)
):
    """
    Busca contatos por nome (Autocomplete) e retorna a situação financeira deles.
    Retorna: Nome, Total a Receber (Devedor) e Total a Pagar (Credor).
    """
    if len(q) < 2:
        return [] # Não busca com menos de 2 letras para poupar banco

    query = (
        select(
            Contato.nome,
            # Soma Receitas Pendentes/Vencidas (Quanto ele nos deve)
            func.sum(case((
                (Titulo.tipo == "RECEITA") & (Titulo.status.in_(["PENDENTE", "VENCIDO"])), 
                Titulo.valor
            ), else_=0)).label("divida_cliente"),
            
            # Soma Despesas Pendentes/Vencidas (Quanto nós devemos a ele)
            func.sum(case((
                (Titulo.tipo == "DESPESA") & (Titulo.status.in_(["PENDENTE", "VENCIDO"])), 
                Titulo.valor
            ), else_=0)).label("credito_fornecedor")
        )
        .join(Titulo.contato)
        .where(Contato.nome.ilike(f"%{q}%")) 
        .group_by(Contato.nome)
    )
    
    result = await db.execute(query)
    dados = result.all()
    
    return [
        {
            "nome": row.nome,
            "a_receber": row.divida_cliente or 0,
            "a_pagar": row.credito_fornecedor or 0
        }
        for row in dados
    ]