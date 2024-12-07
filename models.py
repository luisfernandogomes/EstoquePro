from argon2 import PasswordHasher, verify_password, exceptions
from sqlalchemy import create_engine, Column, Integer, ForeignKey, String, Boolean, DateTime, Float, Date, func
# em baixo importamos session(gerenciar)  e sessiomaker(construir)
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base, relationship
from flask_login import UserMixin
from flask import jsonify


# configura conexao com banco de dados
engine = create_engine('sqlite:///EstoquePro')

# gerencias as sessoes com os banco de dados
db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()
ph = PasswordHasher()


class Usuario(UserMixin, Base):
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(40), unique=False, index=True, nullable=False)
    email = Column(String(80), unique=True, index=True, nullable=False)
    senha = Column(String(80), unique=False, nullable=False, index=True)
    telefone = Column(Integer, unique=True, nullable=False, index=True)
    CNPJ = Column(Integer, unique=True, nullable=True, index=True)
    admin = Column(Boolean, default=False, index=True, nullable=True)
    status = Column(Boolean, default=False, index=True, nullable=True)

    def __repr__(self):
        return '<pessoa: {}, {}, {}, {}, {}>'.format(self.nome, self.email, self.senha,
                                                     self.telefone, self.CNPJ)

    def __init__(self, nome, email, senha, telefone, CNPJ, admin, status):
        self.nome = nome
        self.email = email
        self.senha = ph.hash(senha)
        self.telefone = telefone
        self.CNPJ = CNPJ
        self.admin = admin
        self.status = status

    def verificar_senha(self, senha):
        try:
            return ph.verify(self.senha, senha)  # Verifica se a senha fornecida é válida
        except exceptions.VerifyMismatchError:
            return False

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize_user(self):
        dados_user = {
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'CNPJ_': self.CNPJ
        }

        return dados_user


class Produto(Base):
    __tablename__ = 'produto'

    descricao = Column(String(80), unique=False, index=True, nullable=False)
    id_produto = Column(Integer, primary_key=True, unique=True, nullable=False, index=True, autoincrement=True)
    valor_produto = Column(Float, unique=False, index=False, nullable=False)
    quantidade_produto = Column(Integer, unique=False, nullable=False, index=True)
    categoria_id = Column(Integer, ForeignKey('categoria.id_categoria'), unique=False, nullable=True, index=True)
    categoria = relationship('Categoria')

    def __repr__(self):
        return '<produto: {}, {}, {}, {}, {}>'.format(self.descricao, self.id_produto,
                                                      self.valor_produto, self.quantidade_produto, self.categoria_id)

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize_produto(self):
        dados_produto = {
            'descricao': self.descricao,
            'id_produto': self.id_produto,
            'valor_produto': self.valor_produto,
            'quantidade_produto': self.quantidade_produto,
            'categoria_id': self.categoria_id
        }
        return dados_produto


class Categoria(Base):
    __tablename__ = 'categoria'
    nome = Column(String(80), unique=True, index=True, nullable=False, )
    id_categoria = Column(Integer, primary_key=True, unique=True, nullable=False, index=True, autoincrement=True)

    def __repr__(self):
        return '<categoria: {}, {}>'.format(self.nome, self.id_categoria)

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize_categoria(self):
        dados_categoria = {
            'nome': self.nome,
            'id_categoria': self.id_categoria
        }
        return dados_categoria


class Fornecedor(Base):
    __tablename__ = 'fornecedor'
    nome_fornecedor = Column(String(80), unique=False, index=True, nullable=False)
    CNPJ_fornecedor = Column(Integer, unique=True, index=True, nullable=False)
    id_fornecedor = Column(Integer, primary_key=True, unique=True, nullable=False, index=True, autoincrement=True)

    def __repr__(self):
        return '<fornecedor: {}, {}>'.format(self.nome_fornecedor, self.CNPJ_fornecedor)

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize_fornecedor(self):
        dados_fornecedor = {
            'id_fornecedor': self.id_fornecedor,
            'nome_fornecedor': self.nome_fornecedor,
            'CNPJ_fornecedor': self.CNPJ_fornecedor
        }
        return dados_fornecedor


class Movimentacao_entrada(Base):
    __tablename__ = 'movimentacao_entrada'
    id_movimentacao = Column(Integer, primary_key=True, unique=True, nullable=False, index=True, autoincrement=True)
    quantidade_produto = Column(Integer, unique=False, nullable=False, index=True)
    id_produto = Column(Integer, ForeignKey('produto.id_produto'), index=True, nullable=False)
    data_movimentacao = Column(Date, unique=False, index=True, nullable=False)
    id_funcionario = Column(Integer, ForeignKey('funcionario.id_funcionario'), unique=False, nullable=False, index=True)

    funcionario = relationship('Funcionario')
    produto = relationship('Produto')

    def __repr__(self):
        return '<movimentacao_entrada: {}, {}, {}, {}, {}>'.format(self.id_movimentacao, self.quantidade_produto,
                                                                   self.id_produto, self.data_movimentacao,
                                                                   self.id_funcionario)

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize_movimentacao_entrada(self):
        dados_movimentacao = {
            'id_movimentacao': self.id_movimentacao,
            'quantidade_produto': self.quantidade_produto,
            'id_produto': self.id_produto,
            'data_movimentacao': self.data_movimentacao,
            'id_funcionario': self.id_funcionario
        }
        return dados_movimentacao

# !!!!!
class Movimentacao_saida(Base):
    __tablename__ = 'movimentacao_saida'
    id_movimentacao = Column(Integer, primary_key=True, unique=True, nullable=False, index=True, autoincrement=True)
    data_movimentacao = Column(Date, unique=False, index=True, nullable=False)
    quantidade_produto = Column(Integer, unique=False, nullable=False, index=True)
    id_produto = Column(Integer, ForeignKey('produto.id_produto'), unique=False, nullable=False, index=True)
    id_funcionario = Column(Integer, ForeignKey('funcionario.id_funcionario'), unique=False, nullable=False, index=True)

    funcionario = relationship('Funcionario')
    produto = relationship('Produto')

    def __repr__(self):
        return '<movimentacao_saida: {}, {}, {}, {}, {}>'.format(self.id_movimentacao, self.data_movimentacao,
                                                                 self.quantidade_produto, self.id_produto,
                                                                 self.id_funcionario)

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize_movimentacao_saida(self):
        dados_movimentacao = {
            'id_movimentacao': self.id_movimentacao,
            'data_movimentacao': self.data_movimentacao,
            'quantidade_produto': self.quantidade_produto,
            'id_produto': self.id_produto,
            'id_funcionario': self.id_funcionario
        }
        return dados_movimentacao

# !!!!!
class Funcionario(Base):
    __tablename__ = 'funcionario'
    id_funcionario = Column(Integer, primary_key=True, unique=True, nullable=False, index=True, autoincrement=True)
    nome_funcionario = Column(String(80), unique=False, nullable=False, index=True)
    CPF = Column(String(80), unique=True, nullable=False, index=True)
    salario = Column(Float, unique=False, nullable=False, index=True)

    def __repr__(self):
        return '<funcionario: {}, {}, {}, {}>'.format(self.id_funcionario, self.nome_funcionario, self.CPF,
                                                      self.salario)

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize_funcionario(self):
        dados_funcionario = {
            'id_funcionario': self.id_funcionario,
            'nome_funcionario': self.nome_funcionario,
            'CPF': self.CPF,
            'salario': self.salario
        }
        return dados_funcionario


def init_db():
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    init_db()
