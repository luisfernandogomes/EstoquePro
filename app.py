# import io
#
# import matplotlib.pyplot as plt
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import select, DateTime

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.exc import IntegrityError
import sqlalchemy
from functools import wraps
from models import Produto, db_session, Categoria, Fornecedor, Movimentacao_entrada, Movimentacao_saida, Funcionario, \
    Usuario
from utils import inserir_usuario, inserir_produto, atualizar_produto, inserir_categoria, inserir_fornecedor, \
    inserir_movimentacao_entrada, inserir_movimentacao_saida, inserir_funcionario
from argon2 import PasswordHasher
import base64

ph = PasswordHasher()
app = Flask(__name__)
menager_login = LoginManager(app)
app.secret_key = 'chave_secreta'


@menager_login.user_loader
def user_loader(id):
    usuario = db_session.query(Usuario).filter_by(id=id).first()
    return usuario


menager_login.login_view = 'login'


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.admin:  # Verifica se o usuário NÃO é admin
            flash('Acesso negado, necessita ser admin', 'error')
            return redirect(url_for('home'))  # Redireciona para uma página apropriada
        return f(*args, **kwargs)  # Executa a função original

    return decorated_function


def usuario_ativo(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.status:
            flash('Acesso negado, Usuario desativado', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def redirecionar():
    return redirect(url_for('login'))


#   U          S           U           A            R              I             O          S
# cadastro de usuarios

def verificar_email_cnpj(email, cnpj, telefone):
    usuario = db_session.query(Usuario).filter_by(email=email).first()
    if usuario:
        return True
    usuario = db_session.query(Usuario).filter_by(CNPJ=cnpj).first()
    if usuario:
        return True
    usuario = db_session.query(Usuario).filter_by(telefone=telefone).first()
    if usuario:
        return True
    return False


@app.route('/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        telefone = request.form['telefone']
        CNPJ = request.form['CNPJ']


        if verificar_email_cnpj(email, CNPJ, telefone):
            flash('Email ou CNPJ ja existente', 'error')
            return redirect(url_for('login'), )
        else:
            try:
                if not nome or not email or not senha:
                    flash('preecher todos os campos', 'error')
                else:
                    usuario = Usuario(nome=nome, email=email, senha=senha,
                                      telefone=telefone, CNPJ=CNPJ, admin=False, status=False)
                    db_session.add(usuario)
                    db_session.commit()
                    flash('Usuario cadastrado com sucesso', 'error')
                    return redirect(url_for('login'))
            except IntegrityError:

                flash('erro')

    return render_template("cadastrar_usuario.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        if not email:
            flash('preecher todos os campos', 'error')
        elif not senha:
            flash('preecher todos os campos', 'error')
        else:
            usuario = db_session.query(Usuario).filter_by(email=email).first()
            if not usuario.status:
                flash('usuario desativado')
                redirect(url_for('login'))
            if usuario and usuario.verificar_senha(senha):
                flash('login realizado com sucesso', 'success')
                login_user(usuario)

                return redirect(url_for('home'))
            else:
                flash('login deu errado, certifique-se de que os dados estão coreretos', 'error')

    return render_template("login.html")
# !!!!!!!!!!!!!!!!!!!!!
@app.route('/usuario_editar')
@login_required
@usuario_ativo
@admin_required
def editar_proprio_usuario():
    if request.method == 'POST':
        usuario = db_session.merge(current_user)
        usuario.nome = request.form['nome']
        usuario.email = request.form['email']
        usuario.senha = request.form['senha']
        usuario.telefone = request.form['telefone']
        usuario.CNPJ = request.form['CNPJ']
        usuario.admin = request.form['admin']
        usuario.status = request.form['status']
        usuario.save()
        return redirect(url_for('home'))
    return render_template("editar_perfil_atual.html")
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@app.route('/logout', methods=['GET', 'POST'])
@login_required
@usuario_ativo
def logout():
    logout_user()
    return redirect(url_for('home'))

#
#
# @app.route('/vendas/grafico')
# def vendas_grafico():
#     resultados = vendas_por_mes_ano()
#
#     meses = [resultado.mes_ano for resultado in resultados]
#     totais = [resultado.total_vendas for resultado in resultados]
#
#     # Gerar gráfico
#     img = io.BytesIO()
#     plt.figure(figsize=(10, 6))
#     plt.bar(meses, totais, color='#ff6b6b')
#     plt.xlabel('Mês/Ano')
#     plt.ylabel('Total de Vendas')
#     plt.xticks(rotation=45)
#     plt.tight_layout()
#     plt.savefig(img, format='png')
#     img.seek(0)
#     plot_url = base64.b64encode(img.getvalue()).decode('utf8')
#
#     return render_template('vendas.html', plot_url=plot_url)





# rota para pagina inicial
@app.route('/home')
@login_required
@usuario_ativo
def home():
    lista_categoria = select(Categoria).select_from(Categoria)
    lista_categoria = db_session.execute(lista_categoria).scalars()
    result = []

    for item in lista_categoria:
        result.append(item.serialize_categoria())

    return render_template('home.html', atributos_categoria=result)


# -------------------------------------------------------------------------------------------
# P           R         O            D         U         T           O             S
# cadastro de produtos
@app.route('/produtos/cadastrar', methods=['GET', 'POST'])
@login_required
@admin_required
@usuario_ativo
def cadastrar_produto():
    """
    Página para cadastrar um produto.
    """
    if request.method == 'POST':
        # Obter os dados do produto da requisição
        descricao = request.form.get('descricao')
        valor_produto = request.form.get('valor_produto')

        id_categoria = request.form.get('id_categoria')

        # Verificar se o produto ja foi cadastrado
        produto = db_session.query(Produto).filter_by(descricao=descricao).first()
        if produto:
            # Se sim, mostrar mensagem de erro
            flash('produto ja foi cadastrado, caso deseja adicionar quantidade maior vá em atualizar produto')
            return redirect(url_for('produtos'))
        elif not descricao and not valor_produto:
            flash('você não preencheu nenhum campo sobre o produto', 'error')
        elif not descricao:
            flash('por favor insira o nome do produto', 'error')
        elif not valor_produto:
            flash('por favor insira o valor do produto', 'error')
        else:
            try:
                # Caso contrario, cadastrar o produto
                produto_salvado = Produto(descricao=descricao, valor_produto=valor_produto,
                                          quantidade_produto=0, categoria_id=id_categoria)
                produto_salvado.save()
                flash('produto cadastrado com sucesso')
                return redirect(url_for('produtos'))
            except ValueError as e:
                # Se ocorrer um erro, mostrar mensagem de erro
                flash(str(e))

    # Obter a lista de categorias para o select
    lista_categoria = db_session.execute(select(Categoria)).scalars().all()

    return render_template('cadastrar_produto.html', atributos=lista_categoria)


# exibir produtos
@app.route('/produtos')
@login_required
@usuario_ativo
def produtos():
    # Número de produtos por página
    produtos_por_pagina = 12
    # Obter o número da página a partir da query string (padrão: 1)
    pagina_atual = int(request.args.get('pagina', 1))

    # Calcular o offset
    offset = (pagina_atual - 1) * produtos_por_pagina

    # Selecionar os produtos com limite e offset
    lista_produto = (select(Produto, Categoria)
                     .outerjoin(Categoria, Produto.categoria_id == Categoria.id_categoria)
                     .offset(offset).limit(produtos_por_pagina))
    lista_produtos = db_session.execute(lista_produto).scalars().all()

    result = []

    for item in lista_produtos:
        result.append({'produto': item, 'categoria': item.categoria})

    # Obter o total de produtos para calcular o número de páginas
    total_produtos = db_session.query(Produto).count()
    total_paginas = (total_produtos + produtos_por_pagina - 1) // produtos_por_pagina

    return render_template('produtos.html', atributos_produto=result, pagina_atual=pagina_atual,
                           total_paginas=total_paginas)


@app.route('/produto/atualizar', methods=['GET', 'POST'])
@login_required
@admin_required
@usuario_ativo
def atualizar_produto(descricao=None, descricao_nova=None, valor_produto_novo=None, quantidade_produto_novo=None,
                      valor_produto=None, quantidade_produto=None):
    produto = db_session.query.filter_by(descricao=descricao).first()

    if produto:
        Produto.descricao = descricao_nova

        Produto.valor_produto = valor_produto_novo
        Produto.quantidade_produto = quantidade_produto_novo
        produto.save()
        print(f"descricao: {descricao} atualizado para {descricao_nova}"
              f"valor: {valor_produto} atualizado para {valor_produto_novo}"
              f"quantidade: {quantidade_produto} para {quantidade_produto_novo}")
    else:
        print(f"Fornecedor com nome {descricao} não encontrado.")


# -------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------
#     C                  A                  T             E          G               O           R        I        A

@app.route('/categoria')
@login_required
@usuario_ativo
def categoria():
    categoria_por_pagina = 12
    pagina_atual = int(request.args.get('pagina', 1))
    offset = (pagina_atual - 1) * categoria_por_pagina
    lista_categoria = select(Categoria).select_from(Categoria).offset(offset).limit(categoria_por_pagina)
    lista_categoria = db_session.execute(lista_categoria).scalars()
    result = []

    for item in lista_categoria:
        result.append(item.serialize_categoria())
    total_categoria = db_session.query(Categoria).count()
    total_paginas = (total_categoria + categoria_por_pagina - 1) // categoria_por_pagina
    return render_template('categoria.html', atributos_categoria=result, pagina_atual=pagina_atual, total_paginas=total_paginas )


@app.route('/categoria/cadastrar', methods=['GET', 'POST'])
@login_required
@admin_required
@usuario_ativo
def cadastrar_categoria():
    if request.method == 'POST':
        nome = request.form.get('nome')

        if not nome:
            flash('por favor insira o nome da categoria', 'error')
        else:
            categoria_nome = db_session.execute(select(Categoria).filter_by(nome=nome)).scalar()
            if categoria_nome:
                flash('categoria já cadastrada', 'error')
            else:
                try:
                    Categoria(nome=nome).save()
                    flash('categoria cadastrada com sucesso')
                    return redirect(url_for('categoria'))
                except ValueError as e:
                    flash(str(e))

    return render_template('cadastrar_categoria.html')

@app.route('/categoria/atualizar/<int:id_categoria>', methods=['GET', 'POST'])
def atualizar_categoria(id_categoria):
    categoria_editar = db_session.execute(select(Categoria).where(Categoria.id_categoria == id_categoria)).scalar()
    print(categoria_editar)
    if request.method == 'POST':
        if not request.form.get('nome'):
            flash('preencher nome','error')
        else:
            try:
                categoria_editar.nome = request.form.get('nome')

                categoria_editar.save()
                flash('Categoria editada com sucesso', 'sucesso')
                return redirect(url_for('categoria'))
            except sqlalchemy.exc.IntegrityError:
                flash('Esta Categoria já está cadastrada', 'error')

    return render_template('atualizar_categoria.html', categoria_editado=categoria_editar)




# ----------------------------------------------------------------------------------------------------
#         F              O            R             N          E           C            E          D            O         R
@app.route('/fornecedor')
@login_required
@usuario_ativo
def fornecedor():
    fornecedor_por_pagina = 12
    pagina_atual = int(request.args.get('pagina', 1))
    offset = (pagina_atual - 1) * fornecedor_por_pagina
    lista_fornecedor = select(Fornecedor).select_from(Fornecedor).offset(offset).limit(fornecedor_por_pagina)
    lista_fornecedor = db_session.execute(lista_fornecedor).scalars()
    result = []
    for item in lista_fornecedor:
        result.append(item.serialize_fornecedor())
    total_fornecedor = db_session.query(Fornecedor).count()
    total_paginas = (total_fornecedor + fornecedor_por_pagina - 1) // fornecedor_por_pagina
    return render_template('fornecedor.html', atributos_fornecedor=result, total_paginas=total_paginas, total_fornecedor=total_fornecedor)


@app.route('/fornecedor/cadastrar', methods=['GET', 'POST'])
@login_required
@admin_required
@usuario_ativo
def cadastrar_fornecedor():
    if request.method == 'POST':
        nome_fornecedor = request.form.get('nome_fornecedor')
        CNPJ_fornecedor = request.form.get('CNPJ_fornecedor')
        '''verificação se ja existe algum fornecedor com aquele cnpj'''
        cnpjfornecedor = db_session.execute(select(Fornecedor).filter_by(CNPJ_fornecedor=CNPJ_fornecedor)).scalar()

        try:
            if not nome_fornecedor and not CNPJ_fornecedor:
                flash('você não preencheu nenhum campo')
            elif not nome_fornecedor:
                flash('favor preencher o nome do fornecedor')
                return redirect(url_for('cadastrar_fornecedor'))
            elif not CNPJ_fornecedor:
                flash('favor preencher o cnpj do fornecedor')
                return redirect(url_for('cadastrar_fornecedor'))
            elif cnpjfornecedor:
                flash('fornecedor já cadastrado', 'error')
                return redirect(url_for('fornecedor'))
            else:
                inserir_fornecedor(nome_fornecedor, CNPJ_fornecedor)
                return redirect(url_for('fornecedor'))
        except ValueError as e:
            flash(str(e))
    return render_template('cadastrar_fornecedor.html')


# Lista de itens como exemplo
itens = [
    {'id': 1, 'fornecedor': 'Fornecedor A'},
    {'id': 2, 'fornecedor': 'Fornecedor B'},
    {'id': 3, 'fornecedor': 'Fornecedor C'}
]

def atualizar_fornecedor(itens, item_id, novo_fornecedor):

    for item in itens:
        if item['id'] == item_id:
            item['fornecedor'] = novo_fornecedor
            return f"Fornecedor do item ID {item_id} atualizado para '{novo_fornecedor}'."
    return f"Item com ID {item_id} não encontrado."

# Exemplo de uso
print(atualizar_fornecedor(itens, 2, 'Fornecedor D'))
print(atualizar_fornecedor(itens, 4, 'Fornecedor E'))

# Verificando a lista atualizada
print(itens)


# -----------------------------------------------------------------------------------------------------------------------
#  M     O    V    I     M   E     N     T      A       O           E    N     T     R      A       D       A
# !!!!!
@app.route('/movimentacao_entrada/cadastrar', methods=['GET', 'POST'])
@login_required
@admin_required
@usuario_ativo
def cadastrar_movimentacao_entrada():
    if request.method == 'POST':
        try:
            f_quantidade_produto = int(request.form.get('form_quantidade_produto'))
        except ValueError:
            flash('Quantidade inválida, insira um valor numerico e acima de 0', 'error')
            return redirect(url_for('cadastrar_movimentacao_entrada'))

        try:
            data_movimentacao = datetime.strptime(request.form['form_data_movimentacao'], '%Y-%m-%d').date()
        except ValueError:
            flash('Data inválida. Tente insirir a data no seguinte formato: 2023-06-15', 'error')
            return redirect(url_for('cadastrar_movimentacao_entrada'))
        try:
            f_id_funcionario = int(request.form.get('form_id_funcionario'))
        except ValueError:
            flash('Funcionario com id inválido(VAZIO), selecione um funcionario para realizar a movimentação', 'error')
            return redirect(url_for('cadastrar_movimentacao_entrada'))
        try:
            id_produto = int(request.form.get('form_id_produto'))
        except ValueError:
            flash('Produto com id inválido(VAZIO), selecione um produto para realizar a movimentação', 'error')
            return redirect(url_for('cadastrar_movimentacao_entrada'))


        produto_existente = db_session.execute(select(Produto)
                                               .filter_by(id_produto=id_produto)).scalar()

        quantidade_existente = produto_existente.quantidade_produto

        try:
            movimentacao_entrando = Movimentacao_entrada(quantidade_produto=f_quantidade_produto,
                                                         data_movimentacao=data_movimentacao,
                                                         id_funcionario=f_id_funcionario,
                                                         id_produto=id_produto)

            if produto_existente:
                produto_existente.quantidade_produto = f_quantidade_produto + quantidade_existente

                movimentacao_entrando.save()
                produto_existente.save()
                flash('movimentação realizada com sucesso', 'success')
            return redirect(url_for('movimentacao_entrada'))
        except ValueError as e:
            flash(str(e))
    lista_funcionario = db_session.execute(select(Funcionario)).scalars().all()
    lista_produto = db_session.execute(select(Produto)).scalars().all()
    return render_template('cadastrar_movimentacao_entrada.html',
                           atributos_funcionario=lista_funcionario, atributos_produto=lista_produto)


@app.route('/movimentacao_entrada')
@login_required
@usuario_ativo
def movimentacao_entrada():
    movimentacoes_por_pagina = 12
    pagina_atual = int(request.args.get('pagina_atual', 1))
    offset = (pagina_atual - 1) * movimentacoes_por_pagina


    lista_movimentacao_entrada = (
        select(Movimentacao_entrada, Funcionario)
        .join(Funcionario, Movimentacao_entrada.id_funcionario == Funcionario.id_funcionario)
        .offset(offset).limit(movimentacoes_por_pagina)
    )

    resultado_Movi_Funci = db_session.execute(lista_movimentacao_entrada).fetchall()
    result = []

    for item in resultado_Movi_Funci:
        result.append(item)
    total_movimentacoes = db_session.query(Categoria).count()
    total_paginas = (total_movimentacoes + movimentacoes_por_pagina - 1) // movimentacoes_por_pagina

    return render_template('movimentacao_entrada.html', atributos_movimentacao_entrada=result, total_movimentacoes=total_movimentacoes, total_paginas=total_paginas)


# movimentacao saida sem a exclusao do produto na tabela Produto
@app.route('/movimentacao_saida/cadastrar', methods=['GET', 'POST'])
@login_required
@admin_required
@usuario_ativo
def cadastrar_movimentacao_saida():
    if request.method == 'POST':


        try:
            f_quantidade_produto = int(request.form['form_quantidade_produto'])
        except ValueError:
            flash('Quantidade inválida, insira um valor numerico e acima de 0', 'error')
            return redirect(url_for('cadastrar_movimentacao_entrada'))
        try:
            data_movimentacao = datetime.strptime(request.form['form_data_movimentacao'], '%Y-%m-%d')
        except ValueError:
            flash('Data inválida. Tente insirir a data no seguinte formato: 2023-06-15', 'error')
            return redirect(url_for('cadastrar_movimentacao_entrada'))
        try:
            f_id_funcionario = int(request.form['form_id_funcionario'])
        except ValueError:
            flash('Funcionario com id inválido(VAZIO), selecione um funcionario para realizar a movimentação', 'error')
            return redirect(url_for('cadastrar_movimentacao_entrada'))
        try:
            id_produto = int(request.form['form_id_produto'])
        except ValueError:
            flash('Produto com id inválido(VAZIO), selecione um produto para realizar a movimentação', 'error')
            return redirect(url_for('cadastrar_movimentacao_entrada'))


        produto_existente = db_session.execute(select(Produto).filter_by(id_produto=id_produto)).scalar()
        quantidade_existente = produto_existente.quantidade_produto

        if quantidade_existente >= f_quantidade_produto:

            try:
                movimentacao_saindo = Movimentacao_saida(quantidade_produto=f_quantidade_produto,
                                                         data_movimentacao=data_movimentacao,
                                                         id_funcionario=f_id_funcionario,
                                                         id_produto=id_produto)

                produto_existente.quantidade_produto = quantidade_existente - f_quantidade_produto
                movimentacao_saindo.save()
                produto_existente.save()
                return redirect(url_for('movimentacao_saida'))
            except ValueError as e:
                flash(str(e))
        else:
            flash('a quantidade de produtos inserida é maior que a quantidade existente')
    lista_funcionario = db_session.execute(select(Funcionario)).scalars().all()
    lista_produto = db_session.execute(select(Produto)).scalars().all()

    return render_template('cadastrar_movimentacao_saida.html', atributos_produto=lista_produto, atributos_funcionario=lista_funcionario)


@app.route('/movimentacao_saida')
@login_required
@usuario_ativo
def movimentacao_saida():
    saida_por_pagina = 12
    pagina_atual = int(request.args.get('pagina', 1))
    offset = (pagina_atual - 1) * saida_por_pagina

    lista_movimentacao_saida = (select(Movimentacao_saida, Funcionario, Produto)
                                .join(Funcionario, Movimentacao_saida.id_funcionario == Funcionario.id_funcionario)
                                .join(Produto, Movimentacao_saida.id_produto == Produto.id_produto)
                                .offset(offset).limit(saida_por_pagina)
                                )
    lista_movimentacao_saida = db_session.execute(lista_movimentacao_saida).fetchall()
    result = []

    # for item in lista_movimentacao_saida:
    #     result.append({
    #         'Movimentacao_saida': item, 'Funcionario': item.Funcionario, 'Produto' : item.Produto
    #     })
    print('xxyy', result)
    total_saida = db_session.query(Movimentacao_saida).count()
    total_paginas = (total_saida + saida_por_pagina - 1) // saida_por_pagina

    return render_template('movimentacao_saida.html', atributos_movimentacao_saida=result, total_saida=total_saida, total_paginas=total_paginas)


# -----------------------------------------------------------------------------------------------------------------------
#  F          U         N          C            I          O         N           A          R         I          O
@app.route('/funcionario')
@login_required
@usuario_ativo
def funcionario():
    lista_funcionario = select(Funcionario).select_from(Funcionario)
    lista_funcionario = db_session.execute(lista_funcionario).scalars()
    result = []
    for item in lista_funcionario:
        result.append(item.serialize_funcionario())
    return render_template('funcionario.html', atributos_funcionario=result)


@app.route('/funcionario/cadastrar', methods=['GET', 'POST'])
@login_required
@usuario_ativo
@admin_required
def cadastrar_funcionario():
    if request.method == 'POST':
        nome_funcionario = request.form['nome_funcionario']
        CPF = request.form['CPF']
        salario = request.form['salario']
        funcio = db_session.execute(select(Funcionario).filter_by(CPF=CPF)).scalar()
        if not nome_funcionario and not CPF and not salario:
            flash('nenhum campo foi preenchido, preencher todos os campos', 'error')
        elif not nome_funcionario:
            flash('por favor preencher o nome do funcionario')
        elif not CPF:
            flash('por favor preencher o CPF')
        elif not salario:
            flash('por favor preencher o salario')
        elif len(CPF) != 11:
            flash('CPF inserido é invalido, é necessario 11 digitos')
            redirect(url_for('cadastrar_funcionario'))
        elif funcio:
            flash('funcionario já cadastrado', 'error')
        else:
            try:
                inserir_funcionario(nome_funcionario, CPF, salario)
                return redirect(url_for('funcionario'))
            except ValueError as e:
                flash(str(e))
    return render_template('cadastrar_funcionario.html')


# Lista de funcionários como exemplo
funcionarios = [
    {'id': 1, 'nome': 'Alice', 'cargo': 'Desenvolvedora'},
    {'id': 2, 'nome': 'Bob', 'cargo': 'Gerente'},
    {'id': 3, 'nome': 'Charlie', 'cargo': 'Analista'}
]

def atualizar_funcionario(funcionarios, funcionario_id, novo_nome=None, novo_cargo=None):

    for funcionario in funcionarios:
        if funcionario['id'] == funcionario_id:
            if novo_nome is not None:
                funcionario['nome'] = novo_nome
            if novo_cargo is not None:
                funcionario['cargo'] = novo_cargo
            return f"Funcionário ID {funcionario_id} atualizado com sucesso."
    return f"Funcionário com ID {funcionario_id} não encontrado."

# Exemplo de uso
print(atualizar_funcionario(funcionarios, 2, novo_nome='roberto', novo_cargo='Gerente Sênior'))
print(atualizar_funcionario(funcionarios, 4, novo_nome='Daniele'))

# Verificando a lista atualizada
print(funcionarios)

# -----------------------------------------------------------------------------


if __name__ == '__main__':
    app.run(debug=True)
