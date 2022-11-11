from flask import Flask
from flask_restful import reqparse, Api, Resource, fields

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@localhost/estoqueEmpresa'

db = SQLAlchemy(app)
marshmallow = Marshmallow(app)

class ProdutoDataBase(db.Model):
  __tablename__ = "Produto"
  id = db.Column(db.Integer, primary_key = True)
  nome = db.Column(db.String(256), unique = True, nullable = False)
  quantidade = db.Column(db.Integer, nullable = False)
  preco = db.Column(db.Numeric(precision = 10, scale = 2), nullable = False)

  def __init__(self, nome, quantidade, preco):
    self.nome = nome
    self.quantidade = quantidade
    self.preco = preco

  def create(self):
    db.session.add(self)
    db.session.commit()
    return self

  def __repr__(self):
    return f"{self.id, self.nome, self.quantidade, self.preco}"

class ProdutoDataBaseSchema(marshmallow.SQLAlchemyAutoSchema):
  class Meta:
    model = ProdutoDataBase
    sqla_session = db.session
  
  id = fields.Number()#dump_only=True)
  nome = fields.String(required=True)
  preco = fields.Float(required=True)


api = Api(app)

# Parse dos dados enviados na requisição no formato JSON:
parser = reqparse.RequestParser()
parser.add_argument('id', type=int, help='identificador do produto')
parser.add_argument('nome', type=str, help='nome do produto')
parser.add_argument('quantidade', type=int, help='quantidade do produto')
parser.add_argument('preco', type=float, help='preço do produto')

# Produto:
# 1) Apresenta um único produto.
# 2) Remove um único produto.
# 3) Atualiza (substitui) um produto.
class Produto(Resource):
  def get(self, id):
    produto = ProdutoDataBase.query.get(id)
    produto_schema = ProdutoDataBaseSchema()
    resp = produto_schema.dump(produto)
    return {"produto": resp}, 200 #200: Ok
  
  def delete(self, id):
    produto = ProdutoDataBase.query.get(id)
    db.session.delete(produto)
    db.session.commit()
    return '', 204 #204: No Content
  
  def put(self, id):
    produto_json = parser.parse_args()
    produto = ProdutoDataBase.query.get(id)
    
    if produto_json.get('nome'):
      produto.nome = produto_json.nome
    if produto_json.get('quantidade'):
       produto.quantidade = produto_json.quantidade
    if produto_json.get('preco'):
       produto.preco = produto_json.preco
     
    db.session.add(produto)
    db.session.commit()
    
    produto_schema = ProdutoDataBaseSchema(only=['id', 'nome', 'quantidade', 'preco'])
    resp = produto_schema.dump(produto)
     
    return {"produto": resp}, 200 #200: OK

# ListaProduto:
# 1) Apresenta a lista de produtos.
# 2) Insere um novo produto.
class ListaProduto(Resource):
  def get(self):
    produtos = ProdutoDataBase.query.all()
    produto_schema = ProdutoDataBaseSchema(many=True) # Converter objto Python para JSON.
    resp = produto_schema.dump(produtos)
    return {"produtos": resp}, 200 #200: Ok

  def post(self):
    produto_json = parser.parse_args()
    produto_schema = ProdutoDataBaseSchema()
    produto = produto_schema.load(produto_json)
    produtoDataBase = ProdutoDataBase(produto['nome'], produto['quantidade'], produto['preco'])
    resp = produto_schema.dump(produtoDataBase.create())
    return {"produto": resp}, 201 #201: Created


class ListaValorTotal(Resource):    
    def get(self):
        total = 0
        produto_schema = ProdutoDataBaseSchema()
        produtos = ProdutoDataBase.query.all()
        for produto in produtos:
            prod = produto_schema.dump(produto)
            print (prod)
            total = total + prod["quantidade"] * prod["preco"]
        return total

class ListaQuantidadeProduto(Resource):
    def get(self, id):
        produto_schema = ProdutoDataBaseSchema()
        produtos = ProdutoDataBase.query.all()
        for produto in produtos:
            prod = produto_schema.dump(produto)
            print(prod)
            if prod['id'] == int(id):
                return prod['quantidade']

class ListaQuantidadeTotal(Resource):    
    def get(self):
        total = 0
        produto_schema = ProdutoDataBaseSchema()
        produtos = ProdutoDataBase.query.all()
        for produto in produtos:
            prod = produto_schema.dump(produto)
            print (prod)
            total = total + prod["quantidade"] 
        return total


class Estoque(Resource):
    def get(self):
        produto_schema = ProdutoDataBaseSchema()
        produtos = ProdutoDataBase.query.all()
        prod = produto_schema.dump(produtos[0])
        menor =  prod["quantidade"]
        maior =  prod["quantidade"]

        for produto in produtos:
            prod = produto_schema.dump(produto)
            if prod["quantidade"] < menor:
                menor = prod["quantidade"]
            if prod["quantidade"] > maior:
                maior = prod["quantidade"]          
        dados_estoque = {
            "Menor quantidade": menor,
            "Maior quantidade":maior}
        return dados_estoque

class VendaProduto(Resource):
    def patch(self, id, quantidade):
        produto_schema = ProdutoDataBaseSchema()
        produtos = ProdutoDataBase.query.all()
        for produto in produtos:
            prod = produto_schema.dump(produto)
            if prod['id'] == int(id):
                prod['quantidade'] = prod['quantidade'] - int(quantidade)  
        return prod

class CompraProduto(Resource):
    def patch(self, id, quantidade):
        produto_schema = ProdutoDataBaseSchema()
        produtos = ProdutoDataBase.query.all()
        for produto in produtos:
            prod = produto_schema.dump(produto)
            if prod['id'] == int(id):
                prod['quantidade'] = prod['quantidade'] + int(quantidade)  
        return prod

## Roteamento de recursos: 
## 
api.add_resource(Produto, '/produtos/<id>')
api.add_resource(ListaProduto, '/produtos')
api.add_resource(ListaValorTotal, '/valor/total')
api.add_resource(ListaQuantidadeProduto, '/quantidade/total/<id>')
api.add_resource(ListaQuantidadeTotal, '/quantidade/total')
api.add_resource(Estoque, '/estoque')
api.add_resource(VendaProduto, '/venda/<id>/<quantidade>')
api.add_resource(CompraProduto, '/compra/<id>/<quantidade>')

 
if __name__ == '__main__':
  with app.app_context():
    db.create_all()
  app.run(debug=True)