import asyncio
from sqlalchemy import select, update
from app.database import SessionLocal
from app.modelo import Usuario
from app.seguranca import gerar_hash_senha

async def listar_usuarios():
    async with SessionLocal() as db:
        print("\n --- LISTA DE USUÁRIOS ---")
        result = await db.execute(select(Usuario))
        usuarios = result.scalars().all()
        
        if not usuarios:
            print("Nenhum usuário encontrado.")
            return

        print(f"{'ID':<5} | {'E-MAIL':<30} | {'STATUS DA SENHA'}")
        print("-" * 55)
        for u in usuarios:
            #mostra se está criptografada ou não
            status = "Criptografada (Segura)" if u.senha_hash else "Aberta (Perigo)"
            print(f"{u.id:<5} | {u.email:<30} | {status}")
        print("-" * 55)

async def resetar_senha():
    target_email = input("\nDigite o usuário para trocar a senha: ").strip()
    
    async with SessionLocal() as db:
        # 1. Busca o usuário
        usuario = await db.scalar(select(Usuario).where(Usuario.email == target_email))
        
        if not usuario:
            print(f"Erro: Usuário '{target_email}' não encontrado.")
            return

        # 2. Pede nova senha
        nova_senha = input(f"Digite a NOVA senha para {target_email}: ").strip()
        if not nova_senha:
            print("Operação cancelada.")
            return

        # 3. Atualiza no banco gerando novo Hash
        novo_hash = gerar_hash_senha(nova_senha)
        usuario.senha_hash = novo_hash
        
        db.add(usuario)
        await db.commit()
        print(f" A senha de '{target_email}' foi atualizada")

async def menu():
    while True:
        print("\nFERRAMENTAS ADMINISTRATIVAS")
        print("1. Listar Usuários")
        print("2. Resetar Senha de um Usuário")
        print("0. Sair")
        
        op = input("Opção: ").strip()
        
        if op == "1":
            await listar_usuarios()
        elif op == "2":
            await resetar_senha()
        elif op == "0":
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    asyncio.run(menu())