from models import Usuario, Produto, Categoria, Fornecedor, Movimentacao_entrada, Movimentacao_saida, Funcionario, \
     db_session
from sqlalchemy import select, func



def vendas_por_mes_ano():
    resultados = (
        db_session.query(
            func.strftime('%Y-%m', Movimentacao_entrada.data_movimentacao).label('mes_ano'),
            func.sum(Movimentacao_entrada.id_movimentacao).label('total_movimentacaoes')
        )
        .group_by('mes_ano')
        .order_by('mes_ano')
        .all()
    )
    return resultados














def inserir_usuario(nome, email, senha,  telefone, CNPJ):
    usuario = Usuario(nome=nome, email=email, senha=senha, telefone=telefone, CNPJ=CNPJ)
    print(usuario)
    usuario.save()


def exibir_usuario():
    var_usuario = select(Usuario)
    var_usuario = db_session.execute(var_usuario).all()
    print(var_usuario)


# -----------------------------------------------------------------------------
def inserir_produto(descricao, valor_produto, quantidade_produto, id_categoria):
    produto = Produto(descricao=descricao, valor_produto=valor_produto, quantidade_produto=quantidade_produto, id_categoria=id_categoria)
    print(produto)
    produto.save()


def exibir_produto():
    var_produto = select(Produto)
    var_produto = db_session.execute(var_produto).all()
    print(var_produto)


def deletar_produto():
    produto = Produto.query.filter_by(descricao=Produto.descricao).first()
    print(produto)
    produto.delete()


def atualizar_produto(descricao, valor_produto, quantidade_produto, descricao_nova, valor_produto_novo,
                      quantidade_produto_novo):
    # buscandp produto pela descrição
    produto = Produto.query.filter_by(descricao=descricao).first()

    if produto:
        # Atualizando os dados do fornecedor
        Produto.descricao = descricao_nova
        Produto.valor_produto = valor_produto_novo
        Produto.quantidade_produto = quantidade_produto_novo
        produto.save()
        print(f"descricao: {descricao} atualizado para {descricao_nova},"
              f"valor: {valor_produto} atualizado para {valor_produto_novo}"
              f"quantidade: {quantidade_produto} para {quantidade_produto_novo}")
    else:
        print(f"Fornecedor com nome {descricao} não encontrado.")


# ----------------------------------------------------------------------------------

def inserir_categoria(nome):
    categoria_cadastrada = Categoria(nome=nome)
    print(categoria_cadastrada)
    categoria_cadastrada.save()


def exibir_categoria():
    var_categoria = select(Categoria)
    var_categoria = db_session.execute(var_categoria).all()
    print(var_categoria)

def atualizar_categoria(nome, novo_nome):
    # Primeiro, buscamos o fornecedor pelo nome
    categoria = Categoria.query.filter_by(nome=nome).first()

    if categoria:
        # Atualizamos os dados do fornecedor
        categoria.nome = novo_nome
        categoria.save()
        print(f"Categoria {nome} atualizado para {novo_nome}")
    else:
        print(f"Categoria com nome {nome} não encontrado.")

def deletar_categoria():
    categoria_selecionada = Categoria.query.filter_by(nome=Categoria.nome).first()
    print(categoria_selecionada)
    categoria_selecionada.delete()

# -------------------------------------------------------------------------------------
# fornecedor, inserir, atualizar, exibir, deletar
def inserir_fornecedor(nome_fornecedor, CNPJ_fornecedor ):
    fornecedor_cadastrado = Fornecedor(nome_fornecedor=nome_fornecedor, CNPJ_fornecedor=CNPJ_fornecedor)
    print(fornecedor_cadastrado)
    fornecedor_cadastrado.save()


def exibir_fornecedor():
    fornecedor_atualizado = select(Fornecedor)
    fornecedor_atualizado = db_session.execute(fornecedor_atualizado).all()
    print(fornecedor_atualizado)


def atualizar_fornecedor(nome, novo_nome):
    # Primeiro, buscamos o fornecedor pelo nome
    fornecedor = Fornecedor.query.filter_by(nome=nome).first()

    if fornecedor:
        # Atualizamos os dados do fornecedor
        fornecedor.nome = novo_nome
        fornecedor.save()
        print(f"Fornecedor {nome} atualizado para {novo_nome}")
    else:
        print(f"Fornecedor com nome {nome} não encontrado.")

def deletar_fornecedor():
    fornecedor_selecionada = Fornecedor.query.filter_by(nome=Categoria.nome).first()
    print(fornecedor_selecionada)
    fornecedor_selecionada.delete()
# -------------------------------------------------------------------------------------
# movimentacao entrada, inserir, atualizar, exibir, deletar
def inserir_movimentacao_entrada(quantidade_produto, data_movimentacao,  id_funcionario,
                                 id_produto):
    movimentacao_entrada_cadastrada = Movimentacao_entrada( quantidade_produto=quantidade_produto,
                                                           id_produto=id_produto, data_movimentacao=data_movimentacao, id_funcionario=id_funcionario)
    print(movimentacao_entrada_cadastrada)
    movimentacao_entrada_cadastrada.save()


def exibir_movimentacao_entrada():
    movimentacao_entrada_selecionado = select(Movimentacao_entrada)
    movimentacao_entrada_selecionado = db_session.execute(movimentacao_entrada_selecionado).all()
    print(movimentacao_entrada_selecionado)

def deletar_movimentacao_entrada():
    movimentacao_entrada_selecionada = Movimentacao_entrada.query.filter_by(nome=Movimentacao_entrada.id_movimentacao).first()
    print(movimentacao_entrada_selecionada)
    movimentacao_entrada_selecionada.delete()




# -------------------------------------------------------------------------------------
# movimentacao saida sem a exclusao do produto na tabela Produto, inserir, atualizar, exibir, deletar
def inserir_movimentacao_saida(quantidade_produto, data_movimentacao, id_funcionario, id_produto):
    movimentacao_saida_cadastrada = Movimentacao_saida(quantidade_produto=quantidade_produto,
                                                       data_movimentacao=data_movimentacao,
                                                       id_funcionario=id_funcionario, id_produto=id_produto)
    print(movimentacao_saida_cadastrada)
    movimentacao_saida_cadastrada.save()


def exibir_movimentacao_saida():
    movimentacao_saida_selecionado = select(Movimentacao_saida)
    movimentacao_saida_selecionado = db_session.execute(movimentacao_saida_selecionado).all()
    print(movimentacao_saida_selecionado)

def deletar_movimentacao_saida():
    movimentacao_saida_selecionada = Movimentacao_saida.query.filter_by(nome=Movimentacao_saida.id_movimentacao).first()
    print(movimentacao_saida_selecionada)
    movimentacao_saida_selecionada.delete()

# -------------------------------------------------------------------------------------
# funcionario, inserir, atualizar, exibir, deletar
def inserir_funcionario(nome_funcionario, CPF, salario):
    funcionario_cadastrado = Funcionario(nome_funcionario=nome_funcionario, CPF=CPF, salario=salario)
    print(funcionario_cadastrado)
    funcionario_cadastrado.save()


def exibir_funcionario():
    funcionario_selecionado = select(Funcionario)
    funcionario_selecionado = db_session.execute(funcionario_selecionado).all()
    print(funcionario_selecionado)

def atualizar_funcionario(nome_funcionario, nome_funcionario_novo, CPF, CPF_novo, salario, salario_novo):
    funcionario_selecionado = Funcionario.query.filter_by(nome_funcionario=nome_funcionario).first()
    if funcionario_selecionado:
        Funcionario.nome_funcionario = nome_funcionario_novo
        Funcionario.CPF = CPF_novo
        Funcionario.salario = salario_novo
        print(f"Funcionario {nome_funcionario} atualizado com sucesso para {nome_funcionario_novo}"
              f"CPF {CPF}  atualizado com sucesso para {CPF_novo}"
              f"Salario {salario} atualizado com sucesso para {salario_novo}")
    else:
        print(f" funcionario não encontrado com o nome {nome_funcionario}")

def deletar_funcionario():
    funcionario_selecionada = Funcionario.query.filter_by(nome_funcionario=Funcionario.nome_funcionario).first()
    print(funcionario_selecionada)
    funcionario_selecionada.delete()
# -------------------------------------------------------------------------------------



if __name__ == '__main__':
    # exibir_produto()
    inserir_usuario(nome="Vinicius", email="vinicius@gmail.com", senha="vini123*", telefone="189964752", CNPJ="78541456789")