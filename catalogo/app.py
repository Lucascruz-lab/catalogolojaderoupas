from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from datetime import timedelta
import os
import json

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "segredo123"

SENHA_ADMIN_HASH = "scrypt:32768:8:1$2NVeOlJni1Hxqwc8$feec27c33ce81a165d276ce54944ba673dc4ac5856a7f7a30a69933e613b3df68cbaac53df7112e000eeab530ed8511576fb34067876204ed897f8138a8b3fff"

app.permanent_session_lifetime = timedelta(minutes=30)

ARQUIVO_JSON = os.path.join(os.path.dirname(__file__),"produtos.json")

def ler_produtos():
    with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
        return json.load(f)
    
def salvar_produtos(produtos):
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(produtos, f, indent=4, ensure_ascii=False) 

def criar_produto(form_data, arquivo=None):
    produtos = ler_produtos()

    # Gera código único
    numeros = [int(p["codigo"]) for p in produtos if p.get("codigo") and p["codigo"].isdigit()]
    novo_codigo = str(max(numeros, default=0) + 1).zfill(4)

    preco = float(form_data.get("preco") or 0)
    preco_promocional = float(form_data.get("preco_promocional") or 0)

    caminho_imagem = salvar_arquivo(arquivo) if arquivo else None

    novo_produto = {
        "codigo": novo_codigo,
        "nome": form_data.get("nome"),
        "categoria": form_data.get("categoria"),
        "tamanho": form_data.get("tamanho"),
        "cor": form_data.get("cor"),
        "preco": preco,
        "preco_promocional": preco_promocional if preco_promocional > 0 else None,
        "promocao": preco_promocional > 0,
        "link_wpp": form_data.get("link_wpp"),
        "imagem": caminho_imagem
    }

    produtos.append(novo_produto)
    salvar_produtos(produtos)
    return novo_produto

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__),"static/uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def salvar_arquivo(arquivo):
    if arquivo and arquivo.filename != "":
        nome_arquivo = secure_filename(arquivo.filename)
        pasta_upload = app.config["UPLOAD_FOLDER"]

        caminho = os.path.join(pasta_upload, nome_arquivo)
        contador = 1
        nome, ext = os.path.splitext(nome_arquivo)
        while os.path.exists(caminho):
            nome_arquivo = f"{nome}_{contador}{ext}"
            caminho = os.path.join(pasta_upload, nome_arquivo)
            contador += 1 


        arquivo.save(caminho)
        return f"/static/uploads/{nome_arquivo}"  # caminho relativo para templates
    return None

# ______________ROTAS______________________
@app.route("/")
def home():
    produtos = ler_produtos()
    categorias = list(set([p["categoria"] for p in produtos]))
    return render_template("categorias.html", categorias=categorias)

@app.route("/categoria/<nome>")
def categoria(nome):
    produtos = ler_produtos()
    produtos_da_categoria = [p for p in produtos if p["categoria"].lower() == nome.lower()]
    return render_template("produtos_categoria.html", produtos=produtos_da_categoria, categoria=nome)
# _________ LOGIN ADMIN _______________
@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("admin"):
        return redirect(url_for("admin"))

    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        if "tentativas" not in session:
            session["tentativas"] = 0
        session["tentativas"] += 1
        if session["tentativas"] > 5:
            return render_template("login.html", erro="Muitas tentativas. Tente novamente mais tarde.")        

        if usuario == "admin" and check_password_hash(SENHA_ADMIN_HASH, senha):
            session["admin"] = True
            session["tentativas"] = 0
            session.permanent = True
            return redirect(url_for("admin"))
        else:
            return render_template("login.html", erro="Usuario ou senha incorretos")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))

@app.route("/admin", methods= ["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        criar_produto(request.form)
        return redirect(url_for("admin"))


    produtos = ler_produtos()
    return render_template("admin.html", produtos=produtos)

@app.route("/admin/add", methods=["POST"])
def add_produto():
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    arquivo = request.files.get("imagem")
    criar_produto(request.form, arquivo)
    return redirect(url_for("admin"))
    
@app.route("/admin/delete/<codigo>", methods=["POST"])
def delete_produto(codigo):
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    produtos = ler_produtos()
    produtos = [p for p in produtos if p["codigo"] != codigo] 
    salvar_produtos(produtos)

    return redirect(url_for("admin"))   

@app.route("/admin/edit/<codigo>", methods=["GET", "POST"])
def edit_produto(codigo):
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    produtos = ler_produtos()
    produto = next((p for p in produtos if p["codigo"] == codigo), None)

    if not produto:
        return "Produto não encontrado", 404
    
    if request.method == "POST":
        produto["nome"] = request.form.get("nome")

        produto["categoria"] = request.form.get("categoria")

        produto["tamanho"] = request.form.get("tamanho")

        produto["cor"] = request.form.get("cor")

        produto["preco"] = float(request.form.get("preco"))

        produto["preco_promocional"] = float(request.form.get("preco_promocional") or 0) if request.form.get("preco_promocional") else None

        produto["promocao"] = (produto["preco_promocional"] or 0) > 0

        produto["link_wpp"] = request.form.get("link_wpp")

        arquivo = request.files.get("imagem")
        if arquivo and arquivo.filename != "":
            produto["imagem"] = salvar_arquivo(arquivo)

        salvar_produtos(produtos)
        return redirect(url_for("admin"))
    
    return render_template("edit_produto.html", produto=produto)

@app.route("/catalogo")
def catalogo():
    produtos = ler_produtos()
    categorias = sorted(set([p["categoria"] for p in produtos]))
    return render_template("catalogo.html", produtos=produtos, categorias=categorias)

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    return f"<pre>{traceback.format_exc()}</pre>", 500



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)