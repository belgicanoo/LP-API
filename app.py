from flask import Flask, render_template, request, redirect, url_for, abort
import requests
import json
import os

app = Flask(__name__)

API_KEY = "3e66a5a8486942dd9aa1deee46677f82"
BASE_URL = "https://api.spoonacular.com"
GUARDADOS_FILE = "receitas_guardadas.json"
SEMANA_FILE = "receitas_semana.json"

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

def buscar_receitas(ingredientes_desejados, ingredientes_nao_desejados):
    url = f"{BASE_URL}/recipes/complexSearch"
    params = {
        "apiKey": API_KEY,
        "includeIngredients": ingredientes_desejados,
        "excludeIngredients": ingredientes_nao_desejados,
        "number": 5
    }
    response = requests.get(url, params=params)
    return response.json()

def carregar_receitas_guardadas():
    if not os.path.exists(GUARDADOS_FILE):
        return []
    with open(GUARDADOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_receita(receita):
    receitas = carregar_receitas_guardadas()
    if not any(r['id'] == receita['id'] for r in receitas):
        receitas.append(receita)
        with open(GUARDADOS_FILE, "w", encoding="utf-8") as f:
            json.dump(receitas, f, ensure_ascii=False, indent=2)

def carregar_receitas_semana():
    if not os.path.exists(SEMANA_FILE):
        return {}
    with open(SEMANA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_receita_semana(dia, receita):
    semana = carregar_receitas_semana()
    semana[dia] = receita
    with open(SEMANA_FILE, "w", encoding="utf-8") as f:
        json.dump(semana, f, ensure_ascii=False, indent=2)

def buscar_ingredientes_receita(receita_id):
    url = f"{BASE_URL}/recipes/{receita_id}/information"
    params = {"apiKey": API_KEY, "includeNutrition": False}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None
    data = response.json()
    ingredientes = [ing.get("original") for ing in data.get("extendedIngredients", [])]
    return ingredientes

def carregar_dados_semana():
    if not os.path.exists(SEMANA_FILE):
        return {"receitas": []}
    with open(SEMANA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_dados_semana(dados):
    with open(SEMANA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    ingredientes_desejados = request.form.get('ingredientes_desejados', '').strip()
    ingredientes_nao_desejados = request.form.get('ingredientes_nao_desejados', '').strip()

    if not ingredientes_desejados:
        return render_template('index.html', error="Por favor, insira pelo menos os ingredientes desejados.")

    receitas = buscar_receitas(ingredientes_desejados, ingredientes_nao_desejados)
    receitas_lista = receitas.get('results', [])

    return render_template('index.html', receitas=receitas_lista,
                           ingredientes_desejados=ingredientes_desejados,
                           ingredientes_nao_desejados=ingredientes_nao_desejados)

@app.route('/guardar', methods=['POST'])
def guardar():
    receita_id = request.form.get('id')
    receita_title = request.form.get('title')
    receita_imagem = request.form.get('image')

    if not receita_id or not receita_title or not receita_imagem:
        return redirect(url_for('home'))

    receita = {
        "id": int(receita_id),
        "title": receita_title,
        "image": receita_imagem
    }
    guardar_receita(receita)

    return redirect(url_for('ver_guardadas'))

@app.route('/guardadas')
def ver_guardadas():
    receitas = carregar_receitas_guardadas()
    return render_template('guardadas.html', receitas=receitas)

@app.route('/remover/<int:receita_id>', methods=['POST'])
def remover(receita_id):
    receitas = carregar_receitas_guardadas()
    receitas_filtradas = [r for r in receitas if r['id'] != receita_id]

    with open(GUARDADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(receitas_filtradas, f, ensure_ascii=False, indent=2)

    return redirect(url_for('ver_guardadas'))

@app.route('/atribuir_dia', methods=['POST'])
def atribuir_dia():
    dia = request.form.get('dia')
    receita_id = request.form.get('id')
    receita_title = request.form.get('title')
    receita_imagem = request.form.get('image')

    if dia not in DIAS_SEMANA or not receita_id or not receita_title or not receita_imagem:
        return redirect(url_for('ver_guardadas'))

    receita = {
        "id": int(receita_id),
        "title": receita_title,
        "image": receita_imagem
    }
    guardar_receita_semana(dia, receita)

    return redirect(url_for('ver_guardadas'))

@app.route('/semana')
def mostrar_semana():
    semana = carregar_receitas_semana()
    receitas_completas = {}

    for dia, receita in semana.items():
        ingredientes = buscar_ingredientes_receita(receita["id"])
        receitas_completas[dia] = {
            "info": receita,
            "ingredientes": ingredientes or []
        }

    pode_gerar_lista = len(semana) == 7

    return render_template('semana.html', semana=receitas_completas, dias=DIAS_SEMANA, pode_gerar=pode_gerar_lista)

@app.route('/remover_dia/<dia>', methods=['POST'])
def remover_dia(dia):
    if dia not in DIAS_SEMANA:
        return redirect(url_for('mostrar_semana'))

    semana = carregar_receitas_semana()
    if dia in semana:
        del semana[dia]
        with open(SEMANA_FILE, "w", encoding="utf-8") as f:
            json.dump(semana, f, ensure_ascii=False, indent=2)

    return redirect(url_for('mostrar_semana'))

@app.route('/ingredientes/<int:receita_id>')
def ver_ingredientes(receita_id):
    ingredientes = buscar_ingredientes_receita(receita_id)
    if ingredientes is None:
        abort(404)
    return render_template('ingredientes.html', ingredientes=ingredientes, receita_id=receita_id)

@app.route('/lista_compras')
def lista_compras():
    semana = carregar_receitas_semana()
    if len(semana) != 7:
        return redirect(url_for('mostrar_semana'))

    todos_ingredientes = set()
    for receita in semana.values():
        ingredientes = buscar_ingredientes_receita(receita["id"])
        if ingredientes:
            todos_ingredientes.update(ingredientes)

    lista_ordenada = sorted(todos_ingredientes)
    return render_template('lista_compras.html', ingredientes=lista_ordenada)

@app.route('/comentarios/<int:receita_id>')
def ver_comentarios(receita_id):
    ficheiro = f"comentarios_{receita_id}.json"
    if os.path.exists(ficheiro):
        with open(ficheiro, "r", encoding="utf-8") as f:
            dados = json.load(f)
    else:
        dados = {"comentarios": []}

    comentarios = dados.get("comentarios", [])
    return render_template("comentarios.html", receita_id=receita_id, comentarios=comentarios)

@app.route('/comentarios/<int:receita_id>', methods=['POST'])
def adicionar_comentario(receita_id):
    comentario = request.form.get("comentario", "").strip()

    if not comentario:
        return redirect(url_for("ver_comentarios", receita_id=receita_id))

    ficheiro = f"comentarios_{receita_id}.json"
    if os.path.exists(ficheiro):
        with open(ficheiro, "r", encoding="utf-8") as f:
            dados = json.load(f)
    else:
        dados = {"comentarios": []}

    dados["comentarios"].append(comentario)

    with open(ficheiro, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    return redirect(url_for("ver_comentarios", receita_id=receita_id))

if __name__ == '__main__':
    app.run(debug=True)
