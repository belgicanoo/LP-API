from flask import Flask, render_template, request, redirect, url_for, session
from spoonacular import obter_receitas
from db import get_comentarios, adicionar_comentario
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gerar', methods=['POST'])
def gerar():
    preferencias = {
        'incluidos': request.form.get('incluidos'),
        'excluidos': request.form.get('excluidos'),
        'tipo_refeicao': request.form.get('tipo_refeicao')
    }
    receitas = obter_receitas(preferencias)
    session['receitas'] = receitas
    return render_template('receitas.html', receitas=receitas)

@app.route('/escolher', methods=['POST'])
def escolher():
    receita_id = request.form.get('receita_id')
    for r in session['receitas']:
        if str(r['id']) == receita_id:
            session['favorita'] = r
            break
    return redirect(url_for('receita_final'))

@app.route('/receita_final', methods=['GET', 'POST'])
def receita_final():
    receita = session.get('favorita')
    if not receita:
        return redirect(url_for('index'))

    if request.method == 'POST':
        novo = request.form.get('novo_ingrediente')
        if novo:
            receita['extendedIngredients'].append({'original': novo})
        session['favorita'] = receita

    comentarios = get_comentarios(receita['id'])
    return render_template('receita_final.html', receita=receita, comentarios=comentarios)

@app.route('/comentario/<int:recipe_id>', methods=['POST'])
def comentario(recipe_id):
    texto = request.form.get('comentario')
    if texto:
        adicionar_comentario(recipe_id, texto)
    return redirect(url_for('receita_final'))

if __name__ == '__main__':
    app.run(debug=True)
