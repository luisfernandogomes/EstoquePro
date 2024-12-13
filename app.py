import io
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from sqlalchemy import select, DateTime, func, desc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.exc import IntegrityError
import sqlalchemy
from functools import wraps
from models import Produto, db_session, Categoria, Fornecedor, Movimentacao_entrada, Movimentacao_saida, Funcionario, \
    Usuario, registro_de_acoes_usuers
from utils import inserir_usuario, inserir_produto, atualizar_produto, inserir_categoria, inserir_fornecedor, \
    inserir_movimentacao_entrada, inserir_movimentacao_saida, inserir_funcionario
from argon2 import PasswordHasher
from flask_sqlalchemy import SQLAlchemy

import plotly.express as px
import pandas as pd
import base64

ph = PasswordHasher()
app = Flask(__name__)
menager_login = LoginManager(app)
app.secret_key = 'chave_secreta'


@menager_login.user_loader
def user_loader(id):
    usuario = db_session.query(Usuario).filter_by(id=id).first()
    db_session.close()
    return usuario


# arrumar a estilização no perfil
# e fazer a pagina de gerneciamento de usuarios


menager_login.login_view = 'login'


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.admin:  # Verifica se o usuário NÃO é admin
            flash('Acesso negado, necessita ser admin', 'error')
            return redirect(url_for('index'))  # Redireciona para uma página apropriada
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
    db_session.close()
    return False


@app.route('/index')
@login_required
@usuario_ativo
def index():
    return render_template('index.html')


# =====================================================================================================================

@app.route('/produtos/dados')
def obter_dados_produtos():
    produtos = db_session.query(Produto).all()
    dados = [
        {
            "descricao": produto.descricao,
            "quantidade": produto.quantidade_produto,
            "valor_total": produto.valor_produto * produto.quantidade_produto
        }
        for produto in produtos
    ]
    db_session.close()
    return jsonify(dados)


@app.route('/movimentacoes/dados')
def obter_dados_movimentacoes():
    movimentacoes_entrada = (
        db_session.query(func.date(Movimentacao_entrada.data_movimentacao),
                         func.sum(Movimentacao_entrada.quantidade_produto))
        .group_by(func.date(Movimentacao_entrada.data_movimentacao))
        .all()
    )

    movimentacoes_saida = (
        db_session.query(func.date(Movimentacao_saida.data_movimentacao),
                         func.sum(Movimentacao_saida.quantidade_produto))
        .group_by(func.date(Movimentacao_saida.data_movimentacao))
        .all()
    )

    dados = {
        "entradas": [{"data": str(data), "quantidade": quantidade} for data, quantidade in movimentacoes_entrada],
        "saidas": [{"data": str(data), "quantidade": quantidade} for data, quantidade in movimentacoes_saida]
    }
    db_session.close()
    return jsonify(dados)


# =====================================================================================================================
@app.route('/')
def redirecionar():
    return redirect(url_for('login'))

    #   U          S           U           A            R              I             O          S

    # f       a       z       e       n       d       o       .......
def verificar_cargo(usuario):
    if usuario.admin == True:
        return 'admin'
    elif usuario.gerente == True:
        return 'gerente'
    elif usuario.assistente:
        return 'assistente'
    else:
        return 'sem permissão'
# fazendo gerenciamento de perfis e o perfil atual do usuario

@app.route('/perfil')
@login_required
@usuario_ativo
def perfil():

    usuario = current_user
    cargo = verificar_cargo(usuario)
    total = db_session.query(func.count(registro_de_acoes_usuers.id_acao)) \
        .filter(registro_de_acoes_usuers.user_id == usuario.id) \
        .scalar()
    db_session.close()
    return render_template('perfil.html', usuario=usuario, cargo=cargo, total_de_acoes=total)


# ................................................................

@app.route('/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        telefone = request.form['telefone']
        CNPJ = request.form['CNPJ']

        if verificar_email_cnpj(email, CNPJ, telefone):
            flash('Email ou CNPJ ou telefone ja existente', 'error')
            return redirect(url_for('login'), )
        else:
            try:
                if not nome or not email or not senha:
                    flash('preecher todos os campos', 'error')
                else:
                    usuario = Usuario(nome=nome, email=email, senha=senha,
                                      telefone=telefone, CNPJ=CNPJ, admin=False, status=False,
                                      gerente=False, assistente=False)
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
            flash('Você precisa informar o email', 'error')
            return redirect(url_for('login'))
        elif not senha:
            flash('Voce precisa informar a senha', 'error')
            return redirect(url_for('login'))
        else:
            usuario = db_session.query(Usuario).filter_by(email=email).first()
            if not usuario:
                flash('usuario nao cadastrado')
                return redirect(url_for('login'))
            if not usuario.status:
                flash('usuario desativado')
                return redirect(url_for('login'))
            if usuario and usuario.verificar_senha(senha):
                flash('login realizado com sucesso', 'success')
                login_user(usuario)

                return redirect(url_for('index'))
            else:
                flash('login deu errado, certifique-se de que os dados estão coreretos', 'error')
    db_session.close()
    return render_template("login.html")


@app.route('/logout', methods=['GET', 'POST'])
@login_required
@usuario_ativo
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/home')
@login_required
@usuario_ativo
def home():
    lista_categoria = select(Categoria).select_from(Categoria)
    lista_categoria = db_session.execute(lista_categoria).scalars()
    result = []

    for item in lista_categoria:
        result.append(item.serialize_categoria())
    db_session.close()
    return render_template('home.html', atributos_categoria=result)


# -------------------------------------------------------------------------------------------
# P           R         O            D         U         T           O             S
# cadastro de produtos
@app.route('/produtos/cadastrar', methods=['GET', 'POST'])
@login_required
@admin_required
@usuario_ativo
def cadastrar_produto():
    if request.method == 'POST':

        descricao = request.form.get('descricao')
        valor_produto = float(request.form.get('valor_produto'))

        id_categoria = int(request.form.get('id_categoria'))

        # Verificar se o produto ja foi cadastrado
        produto = db_session.query(Produto).filter_by(descricao=descricao).first()
        if produto:
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

                produto_salvado = Produto(descricao=descricao, valor_produto=valor_produto,
                                          quantidade_produto=0, categoria_id=id_categoria)
                produto_salvado.save()

                acao_registrado = registro_de_acoes_usuers(user_id=current_user.id,
                                                           user_name=current_user.nome,
                                                           acao=f"cadastrou produto '{produto_salvado.descricao}'"
                                                                f" com valor {produto_salvado.valor_produto} na categoria {produto_salvado.categoria_id}",
                                                           objeto_alterado="produto",
                                                           id_do_objeto_alterado=produto_salvado.id_produto,
                                                           data_acao=datetime.utcnow())
                acao_registrado.save()
                flash('produto cadastrado com sucesso')
                return redirect(url_for('produtos'))
            except ValueError as e:

                flash(str(e))

    lista_categoria = db_session.execute(select(Categoria)).scalars().all()
    db_session.close()
    return render_template('cadastrar_produto.html', atributos=lista_categoria)


@app.route('/produtos')
@login_required
@usuario_ativo
def produtos():
    produtos_por_pagina = 1000

    pagina_atual = int(request.args.get('pagina', 1))

    offset = (pagina_atual - 1) * produtos_por_pagina

    lista_produto = (select(Produto, Categoria)
                     .outerjoin(Categoria, Produto.categoria_id == Categoria.id_categoria)
                     .order_by(desc(Produto.quantidade_produto))
                     .offset(offset).limit(produtos_por_pagina))
    lista_produtos = db_session.execute(lista_produto).scalars().all()

    result = []

    for item in lista_produtos:
        result.append({'produto': item, 'categoria': item.categoria})

    total_produtos = db_session.query(Produto).count()
    total_paginas = (total_produtos + produtos_por_pagina - 1) // produtos_por_pagina
    db_session.close()
    return render_template('produtos.html', atributos_produto=result, pagina_atual=pagina_atual,
                           total_paginas=total_paginas)


@app.route('/produto/atualizar/<int:id_produto>', methods=['GET', 'POST'])
@login_required
@admin_required
@usuario_ativo
def atualizar_produto(id_produto):
    atributos_categoria = db_session.execute(select(Categoria)).scalars().all()
    produto_editar = db_session.execute(select(Produto).where(Produto.id_produto == id_produto)).scalar()

    if request.method == 'POST':
        if not request.form.get('descricao'):
            flash('preencher descricao do produto')
        elif not request.form.get('valor_produto'):
            flash('preencher valor do produto')
        elif not request.form.get('categoria_id'):
            flash('preencher categoria do produto')
        try:
            produto_editar.descricao = request.form.get('descricao')
        except sqlalchemy.exc.IntegrityError:
            flash('descricao ja cadastrado', 'error')
        try:
            produto_editar.valor_produto = float(request.form.get('valor_produto'))
        except ValueError:
            flash('valor do produto invalido')
        except sqlalchemy.exc.IntegrityError:
            flash('valor do produto invalido')

        try:
            produto_editar.categoria_id = request.form.get('categoria_id')

        except sqlalchemy.exc.IntegrityError:
            print('categoria do produto invalida')
        print(f'xyyyy{produto_editar.categoria_id}')
        produto_editar.save()
        return redirect(url_for('produtos'))
    db_session.close()
    return render_template('atualizar_produto.html', produto_editado=produto_editar,
                           atributos_categoria=atributos_categoria)


@app.route('/produto/deletar/<int:id_produto>', methods=['GET', 'POST'])
@login_required
@admin_required
@usuario_ativo
def deletar_produto(id_produto):
    produto_deletar = db_session.execute(select(Produto).where(Produto.id_produto == id_produto)).scalar()
    if request.method == 'POST':

        acao = request.form.get('acao')
        if acao == 'cancelar':
            return redirect(url_for('produtos'))
        elif acao == 'deletar':
            if produto_deletar.quantidade_produto > 0:
                flash('produto com quantidade maior que 0, impossivel deletar', 'error')

            else:
                produto_deletar.delete()
                return redirect(url_for('produtos'))
    db_session.close()
    return render_template('deletar_produto.html', produto_deletar=produto_deletar)


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
    db_session.close()
    return render_template('categoria.html', atributos_categoria=result, pagina_atual=pagina_atual,
                           total_paginas=total_paginas)


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
    db_session.close()
    return render_template('cadastrar_categoria.html')


@app.route('/categoria/atualizar/<int:id_categoria>', methods=['GET', 'POST'])
def atualizar_categoria(id_categoria):
    categoria_editar = db_session.execute(select(Categoria).where(Categoria.id_categoria == id_categoria)).scalar()
    print(categoria_editar)
    if request.method == 'POST':
        if not request.form.get('nome'):
            flash('preencher nome', 'error')
        else:
            try:
                categoria_editar.nome = request.form.get('nome')
                categoria_editar.save()
                flash('Categoria editada com sucesso', 'sucesso')
                return redirect(url_for('categoria'))
            except sqlalchemy.exc.IntegrityError:
                flash('Esta Categoria já está cadastrada', 'error')
    db_session.close()
    return render_template('atualizar_categoria.html', categoria_editado=categoria_editar)


@app.route('/categoria/deletar/<int:id_categoria>', methods=['GET', 'POST'])
def deletar_categoria(id_categoria):
    categoria_deletar = db_session.execute(select(Categoria).where(Categoria.id_categoria == id_categoria)).scalar()
    if request.method == 'POST':
        acao = request.form.get('acao')
        if acao == 'cancelar':
            return redirect(url_for('categoria'))
        elif acao == 'deletar':
            if categoria_deletar.relacao_produtos:
                flash('categoria com produtos cadastrados, impossivel deletar', 'error')
            elif not categoria_deletar.relacao_produtos:
                categoria_deletar.delete()
                return redirect(url_for('categoria'))
    db_session.close()
    return render_template('deletar_categoria.html', categoria_deletar=categoria_deletar)


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
    db_session.close()
    return render_template('fornecedor.html', atributos_fornecedor=result, total_paginas=total_paginas,
                           total_fornecedor=total_fornecedor)


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
    db_session.close()
    return render_template('cadastrar_fornecedor.html')


@app.route('/fornecedor/atualizar/<int:id_fornecedor>', methods=['GET', 'POST'])
def atualizar_fornecedor(id_fornecedor):
    fornecedor_editar = db_session.execute(select(Fornecedor).where(Fornecedor.id_fornecedor == id_fornecedor)).scalar()
    if request.method == 'POST':
        if not request.form.get('nome_fornecedor'):
            flash('preeencher o nome do fornecedor')
        elif not request.form.get('CNPJ_fornecedor'):
            flash('preeencher o CNPJ do fornecedor')
        else:
            try:
                fornecedor_editar.nome_fornecedor = request.form.get('nome_fornecedor')
            except sqlalchemy.exc.IntegrityError:
                flash('Este fornecedor já está cadastrado')
            try:
                fornecedor_editar.CNPJ_fornecedor = request.form.get('CNPJ_fornecedor')
                fornecedor_editar.save()
                return redirect(url_for('fornecedor'))
            except sqlalchemy.exc.IntegrityError:
                flash('CNPJ já cadastrado em outro usuario')
    db_session.close()
    return render_template('atualizar_fornecedor.html', fornecedor_editado=fornecedor_editar)


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
    db_session.close()
    return render_template('cadastrar_movimentacao_entrada.html',
                           atributos_funcionario=lista_funcionario, atributos_produto=lista_produto)


@app.route('/movimentacao_entrada')
@login_required
@usuario_ativo
def movimentacao_entrada():
    movimentacoes_por_pagina = 9
    pagina_atual = int(request.args.get('pagina_atual', 1))
    offset = (pagina_atual - 1) * movimentacoes_por_pagina

    lista_movimentacao_entrada = (
        select(Movimentacao_entrada, Funcionario, Fornecedor)
        .join(Funcionario, Movimentacao_entrada.id_funcionario == Funcionario.id_funcionario)
        .join(Fornecedor, Movimentacao_entrada.fornecedor == Fornecedor.id_fornecedor)
        .offset(offset).limit(movimentacoes_por_pagina)
    )

    resultado_Movi_Funci = db_session.execute(lista_movimentacao_entrada).fetchall()
    total_movimentacoes = db_session.query(Movimentacao_entrada).count()
    total_paginas = (total_movimentacoes + movimentacoes_por_pagina - 1) // movimentacoes_por_pagina
    db_session.close()

    return render_template('movimentacao_entrada.html', atributos_movimentacao_entrada=resultado_Movi_Funci,
                           total_movimentacoes=total_movimentacoes, total_paginas=total_paginas,
                           pagina_atual=pagina_atual)


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
    db_session.close()
    return render_template('cadastrar_movimentacao_saida.html', atributos_produto=lista_produto,
                           atributos_funcionario=lista_funcionario)


@app.route('/movimentacao_saida')
@login_required
@usuario_ativo
def movimentacao_saida():
    saida_por_pagina = 9
    pagina_atual = int(request.args.get('pagina', 1))
    offset = (pagina_atual - 1) * saida_por_pagina

    lista_movimentacao_saida = (select(Movimentacao_saida, Funcionario, Produto)
                                .join(Funcionario, Movimentacao_saida.id_funcionario == Funcionario.id_funcionario)
                                .join(Produto, Movimentacao_saida.id_produto == Produto.id_produto)
                                .offset(offset).limit(saida_por_pagina)
                                )
    lista_movimentacao_saida = db_session.execute(lista_movimentacao_saida).fetchall()
    result = []

    print('xxyy', result)
    total_saida = db_session.query(Movimentacao_saida).count()
    total_paginas = (total_saida + saida_por_pagina - 1) // saida_por_pagina
    db_session.close()
    return render_template('movimentacao_saida.html', atributos_movimentacao_saida=lista_movimentacao_saida,
                           total_saida=total_saida,
                           total_paginas=total_paginas,
                           pagina_atual=pagina_atual)


# -----------------------------------------------------------------------------------------------------------------------
#  F          U         N          C            I          O         N           A          R         I          O
@app.route('/funcionario')
@login_required
@usuario_ativo
@admin_required
def funcionario():
    lista_funcionario = select(Funcionario).select_from(Funcionario)
    lista_funcionario = db_session.execute(lista_funcionario).scalars()
    result = []
    for item in lista_funcionario:
        result.append(item.serialize_funcionario())
    db_session.close()
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
    db_session.close()
    return render_template('cadastrar_funcionario.html')


@app.route('/funcionario/atualizar/<int:id_funcionario>', methods=['GET', 'POST'])
def atualizar_funcionario(id_funcionario):
    funcionario_editar = db_session.execute(
        select(Funcionario).where(Funcionario.id_funcionario == id_funcionario)).scalar()
    if request.method == 'POST':
        if not request.form.get('nome_funcionario'):
            flash('preeencher o nome do funcionario')
        elif not request.form.get('CPF'):
            flash('preeencher o CPF')
        elif not request.form.get('salario'):
            flash('preeencher o salario')
        else:
            try:
                funcionario_editar.nome_funcionario = request.form.get('nome_funcionario')
            except sqlalchemy.exc.IntegrityError:
                flash('Este funcionario já está cadastrado')
            try:
                funcionario_editar.CPF = request.form.get('CPF')
            except sqlalchemy.exc.IntegrityError:
                flash('CPF já cadastrado em outro usuario')
            try:
                funcionario_editar.salario = request.form.get('salario')
                funcionario_editar.save()
                return redirect(url_for('funcionario'))
            except sqlalchemy.exc.IntegrityError:
                flash('atualização inconcistente')
    db_session.close()
    return render_template('atualizar_funcionario.html', funcionario_editado=funcionario_editar)


# -----------------------------------------------------------------------------


if __name__ == '__main__':
    app.run(debug=True)
