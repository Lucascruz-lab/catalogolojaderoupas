from flask import Flask, render_template, request, session, redirect, url_for
import json

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.secret_key = "segredo123"

ARQUIVO_JSON = "backend/produtos.json"

def ler_produtos():
    with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
        return json.load(f)
    
def salvar_produtos(produtos):
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(produtos, f, indent=4, ensure_ascii=False)    
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
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        if usuario == "admin" and senha == "123":
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            return render_template("login.html", erro="Usuario ou senha incorretos")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    produtos = ler_produtos()
    return render_template("admin.html", produtos=produtos)

@app.route("/admin/add", methods=["POST"])
def add_produto():
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    produtos=ler_produtos 
    novo = {
        "codigo": request.form["codigo"],
        "nome": request.form["nome"],
        "categoria": request.form["categoria"],
        "tamanho": request.form["tamanho"],
        "cor": request.form["cor"],
        "preco": request.form["preco"],
        "promocao": request.form["promocao"] == "on",
        "link_wpp": request.form["link_wpp"],
    }

    produtos.append(novo)
    salvar_produtos(produtos)

    return redirect(url_for("admin"))
    


if __name__ == "__main__":
    app.run(debug=True)