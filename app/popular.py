import asyncio
import os
import random
import sys
import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.database import SessionLocal
from app.modelo import Usuario, Categoria, Contato, ContaBancaria, Titulo, TipoLancamento, StatusTitulo, Anexo
from app.seguranca import gerar_hash_senha


BANCOS_BRASIL = [
    "Banco do Brasil", "Caixa Econômica", "Itaú", "Bradesco",
    "Santander", "Nubank", "Inter", "C6 Bank", "BTG Pactual",
    "Safra", "Votorantim", "Banco Pan", "Original", "Banrisul", 
    "Banco do Nordeste", "Citibank", "Daycoval", "Sicredi", "Sicoob"
]

# GERADOR DE NOMES DE EMPRESAS para criar contatos infinitos
PREFIXOS = ["Tech", "Global", "Omega", "Alfa", "Beta", "Super", "Mega", "Ultra", "Prime", "Fast", "Easy", "Star"]
RAMOS = ["Soluções", "Sistemas", "Logística", "Varejo", "Consultoria", "Engenharia", "Alimentos", "Marketing", "Financeira"]
SUFIXOS = ["Ltda", "S.A.", "ME", "EIRELI", "Group", "Brasil", "Internacional", "Tech", "Digital"]

def gerar_nome_empresa_fake():
    return f"{random.choice(PREFIXOS)} {random.choice(RAMOS)} {random.choice(SUFIXOS)}"

def gerar_cnpj_fake():
    # Gera um número aleatório formatado como CNPJ
    return f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}"

# CATEGORIAS PADRÃO
CATEGORIAS_MOCK = [
    {"nome": "Vendas de Produtos", "tipo": "RECEITA"},
    {"nome": "Serviços Prestados", "tipo": "RECEITA"},
    {"nome": "Rendimentos Aplicações", "tipo": "RECEITA"},
    {"nome": "Infraestrutura/Cloud", "tipo": "DESPESA"},
    {"nome": "Marketing e Publicidade", "tipo": "DESPESA"},
    {"nome": "Folha de Pagamento", "tipo": "DESPESA"},
    {"nome": "Impostos e Taxas", "tipo": "DESPESA"},
    {"nome": "Fornecedores de Matéria Prima", "tipo": "DESPESA"},
    {"nome": "Aluguel e Condomínio", "tipo": "DESPESA"},
    {"nome": "Manutenção e Limpeza", "tipo": "DESPESA"},
]

async def verificar_admin_existe(db: AsyncSession) -> bool:
    result = await db.execute(select(Usuario))
    usuario = result.scalars().first()
    if not usuario:
        print(f"\n[!] ALERTA: Nenhum administrador encontrado.")
        return False
    return True

async def criar_admin_manual(db: AsyncSession):
    print("\n--- CRIAR NOVO ADMINISTRADOR ---")
    email = input("Digite o usuário do administrador: ").strip()
    senha = input("Digite a Senha: ").strip()
    if not email or not senha: return

    existente = await db.scalar(select(Usuario).where(Usuario.email == email))
    if existente:
        print("Erro: Esse usuário já existe.")
        return

    admin = Usuario(email=email, senha_hash=gerar_hash_senha(senha))
    db.add(admin)
    await db.commit()
    print(f"Usuário {email} criado.")

async def gerar_dados_ficticios(db: AsyncSession):
    try:
        qtd_input = input("\nQuantos lançamentos simular? (Recomendado: 500): ")
        qtd = int(qtd_input) if qtd_input else 500
    except ValueError:
        qtd = 500

    print(f"\n🚀 Iniciando simulação de carga com {qtd} registros...")

    # 1. BANCOS (Cria entre 5 e 10 bancos ativos para a empresa)
    print("   -> Verificando/Criando Contas Bancárias...")
    result_contas = await db.execute(select(ContaBancaria))
    contas_existentes = result_contas.scalars().all()

    if len(contas_existentes) < 5:
        # Seleciona 8 bancos aleatórios para criar
        bancos_selecionados = random.sample(BANCOS_BRASIL, 8)
        for nome_banco in bancos_selecionados:
            # Verifica se já não existe pelo nome (descricao unique)
            desc = f"Conta PJ - {nome_banco}"
            existe = await db.scalar(select(ContaBancaria).where(ContaBancaria.descricao == desc))
            
            if not existe:
                saldo_fake = Decimal(random.randint(10000, 500000))
                nova_conta = ContaBancaria(
                    descricao=desc,
                    nome_banco=nome_banco,
                    saldo_inicial=saldo_fake
                )
                db.add(nova_conta)
        await db.commit()
        result_contas = await db.execute(select(ContaBancaria))
        contas_existentes = result_contas.scalars().all()

    # 2. CATEGORIAS
    print("   -> Garantindo Categorias Financeiras...")
    for cat in CATEGORIAS_MOCK:
        obj = await db.scalar(select(Categoria).where(Categoria.nome == cat["nome"]))
        if not obj:
            obj = Categoria(nome=cat["nome"], descricao="Gerado auto")
            db.add(obj)
    await db.commit()
    # Mapa para saber o tipo (Receita/Despesa) pelo nome
    mapa_tipos = {c["nome"]: c["tipo"] for c in CATEGORIAS_MOCK}
    categorias_db = (await db.execute(select(Categoria))).scalars().all()

    # 3. CONTATOS (Aqui está a simulação real: Volume alto)
    # criar um número de contatos proporcional aos lançamentos (30% do volume)
    # Isso simula clientes recorrentes e novos clientes
    qtd_contatos = int(qtd * 0.3) 
    if qtd_contatos < 10: qtd_contatos = 10
    
    print(f"   -> Gerando {qtd_contatos} Empresas/Contatos Fakes...")
    
    contatos_para_adicionar = []
    for _ in range(qtd_contatos):
        nome_fake = gerar_nome_empresa_fake()
        # evita duplicados na lista de inserção
        if not any(c.nome == nome_fake for c in contatos_para_adicionar):
            contatos_para_adicionar.append(
                Contato(nome=nome_fake, documento=gerar_cnpj_fake())
            )
    
    db.add_all(contatos_para_adicionar)
    await db.commit()
    
    # Pega todos os contatos do banco (incluindo antigos) para misturar tudo
    contatos_db = (await db.execute(select(Contato))).scalars().all()

    # 4. TÍTULOS E ANEXOS
    print(f"   -> Gerando {qtd} Lançamentos com Anexos...")
    
    hoje = date.today()
    
    for i in range(qtd):
        categoria = random.choice(categorias_db)
        contato = random.choice(contatos_db)
        conta = random.choice(contas_existentes)
        
        tipo_str = mapa_tipos.get(categoria.nome, "DESPESA")
        tipo_enum = TipoLancamento.RECEITA if tipo_str == "RECEITA" else TipoLancamento.DESPESA
        
        # Distribuição de Datas: 
        # 60% Passado (Histórico), 10% Hoje, 30% Futuro (Projeção)
        sorteio_data = random.random()
        if sorteio_data < 0.6:
            dias = random.randint(-90, -1) # Passado
        elif sorteio_data < 0.7:
            dias = 0 # Hoje
        else:
            dias = random.randint(1, 60) # Futuro
            
        vencimento = hoje + timedelta(days=dias)
        
        # Valores realistas (maioria valores baixos, poucos valores altos)
        if random.random() < 0.8:
            valor = Decimal(random.randint(50, 2000))
        else:
            valor = Decimal(random.randint(2000, 15000))
        
        # Status Lógico
        status = StatusTitulo.PENDENTE
        data_pag = None
        
        if vencimento <= hoje:
            # Se já venceu, grande chance de estar pago, pequena de estar vencido
            if random.random() < 0.85: 
                status = StatusTitulo.PAGO
                # Pagou entre 5 dias antes e 5 dias depois do vencimento
                delta_pag = random.randint(-5, 5)
                data_pag = vencimento + timedelta(days=delta_pag)
            else:
                status = StatusTitulo.VENCIDO
        
        t = Titulo(
            descricao=f"Ref. {categoria.nome} - Nota {random.randint(1000, 9999)}",
            valor=valor,
            data_vencimento=vencimento,
            data_pagamento=data_pag,
            tipo=tipo_enum,
            status=status,
            categoria_id=categoria.id,
            contato_id=contato.id,
            conta_bancaria_id=conta.id,
            numero_parcela=1,
            total_parcelas=1
        )
        db.add(t)
        
        # Flush para gerar o ID do título e podermos criar o anexo
        await db.flush()
        
        # Simulação de Anexo (80% dos lançamentos têm comprovante)
        if random.random() < 0.8:
            ext = random.choice(['pdf', 'png', 'jpg'])
            anexo = Anexo(
                nome_arquivo=f"comprovante_{t.id}.{ext}",
                caminho_arquivo=f"s3://bucket-financeiro/docs/{date.today().year}/{t.id}.{ext}",
                titulo_id=t.id
            )
            db.add(anexo)
            
        # Commit em lotes pequenos para não estourar memória se for muuuito dado
        if i % 100 == 0:
            await db.commit()
    
    await db.commit()
    print("\n" + "="*50)
    print(f"SIMULAÇÃO CONCLUÍDA COM SUCESSO!")
    print(f"Resumo do Cenário:")
    print(f"   - Títulos Gerados: {qtd}")
    print(f"   - Contatos Ativos: {len(contatos_db)} (Mix de Clientes/Fornecedores)")
    print(f"   - Bancos Usados:   {len(contas_existentes)}")
    print("="*50 + "\n")

async def menu_principal():
    async with SessionLocal() as db:
        while True:
            tem_admin = await verificar_admin_existe(db)

            print("\n" + "="*40)
            print("   GERENCIADOR DE CARGA (SEED)")
            print("="*40)
            
            if not tem_admin:
                print("1. Criar Administrador")
            
            print("2. Popular Banco (Simulação Realista)")
            print("0. Sair")
            
            opcao = input("Escolha uma opção: ").strip()
            
            if opcao == "1" and not tem_admin:
                await criar_admin_manual(db)
            elif opcao == "2":
                await gerar_dados_ficticios(db)
            elif opcao == "0":
                print("Saindo...")
                break
            else:
                print("Opção inválida.")

if __name__ == "__main__":
    if not sys.stdin.isatty():
        print("Modo não interativo detectado.")
    else:
        asyncio.run(menu_principal())