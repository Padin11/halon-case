import uuid
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List

from app.modelo import Titulo, StatusTitulo
from app.schemas import TituloCreate

def criar_titulos_parcelados(dados: TituloCreate) -> List[Titulo]:
    
    #Gera a lista de objetos Titulo (SQLAlchemy) baseado no input.
    #Resolve dois problemas clássicos:
    #1. A diferença de centavos na divisão (R$ 100 em 3x).
    #2. O incremento correto de meses (dia 31 + 1 mês = dia 30 ou 28/29).
    
    
    lista_titulos = []
    
    # Se não for parcelado, segue
    if not dados.parcelado or dados.total_parcelas <= 1:
        titulo_unico = Titulo(
            descricao=dados.descricao,
            valor=dados.valor,
            data_vencimento=dados.data_vencimento,
            tipo=dados.tipo,
            status=StatusTitulo.PENDENTE,
            categoria_id=dados.categoria_id,
            contato_id=dados.contato_id,
            conta_bancaria_id=dados.conta_bancaria_id,
            numero_parcela=1,
            total_parcelas=1,
            id_transacao_pai=None
        )
        return [titulo_unico]

    # LÓGICA DE PARCELAMENTO
    
    # Gera um ID único para amarrar todas as parcelas
    id_agrupamento = uuid.uuid4()
    
    # 1. Calcula o valor base (arredondando para baixo em 2 casas)
    valor_parcela = round(dados.valor / dados.total_parcelas, 2)
    
    # 2. Calcula a diferença de centavos (ex: 100 - (33.33 * 3) = 0.01)
    soma_parcelas = valor_parcela * dados.total_parcelas
    diferenca = dados.valor - soma_parcelas
    
    data_base = dados.data_vencimento

    for i in range(dados.total_parcelas):
        numero = i + 1
        
        # A primeira parcela leva a diferença
        valor_desta_parcela = valor_parcela
        if numero == 1:
            valor_desta_parcela += diferenca
            
        # Cálculo da data: Incrementa X meses corretamente usando dateutil
        nova_vencimento = data_base + relativedelta(months=i)
        
        titulo = Titulo(
            descricao=f"{dados.descricao} ({numero}/{dados.total_parcelas})",
            valor=valor_desta_parcela,
            data_vencimento=nova_vencimento,
            tipo=dados.tipo,
            status=StatusTitulo.PENDENTE,
            categoria_id=dados.categoria_id,
            contato_id=dados.contato_id,
            conta_bancaria_id=dados.conta_bancaria_id,
            numero_parcela=numero,
            total_parcelas=dados.total_parcelas,
            id_transacao_pai=id_agrupamento
        )
        lista_titulos.append(titulo)
        
    return lista_titulos