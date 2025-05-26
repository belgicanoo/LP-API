from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
from urllib.parse import unquote
from pymongo import MongoClient

app = Flask(__name__)

API_KEY = '102e440d05e14a75b434d6de15670598'

# Conexão MongoDB local (assumindo rodando no localhost:27017)
client = MongoClient('mongodb://localhost:27017/')
db = client.recipe_app
comments_col = db.comments

@app.route('/home', methods=['GET'])
def home():
    return render_template('index.html', recipes=[], search_query='')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        query = request.form.get('search_query', '')
        liked = request.form.get('liked_ingredients', '')
        disliked = request.form.get('disliked_ingredients', '')

        if action == 'Buscar Receitas':
            recipes = search_recipes(query)
            return render_template('index.html', recipes=recipes, search_query=query)

        elif action == 'Gerar Plano Alimentar':
            return redirect(url_for('meal_plan_route', liked=liked, disliked=disliked))

    search_query = request.args.get('search_query', '')
    decoded_search_query = unquote(search_query)
    recipes = search_recipes(decoded_search_query)
    return render_template('index.html', recipes=recipes, search_query=decoded_search_query)

def search_recipes(query):
    url = 'https://api.spoonacular.com/recipes/complexSearch'
    params = {
        'apiKey': API_KEY,
        'query': query,
        'number': 10,
        'instructionsRequired': True,
        'addRecipeInformation': True,
        'fillIngredients': True,
    }
    response = requests.get(url, params=params)
    return response.json().get('results', []) if response.status_code == 200 else []

@app.route('/meal-plan')
def meal_plan_route():
    liked = request.args.get('liked', '')
    disliked = request.args.get('disliked', '')

    url = 'https://api.spoonacular.com/mealplanner/generate'
    params = {
        'apiKey': API_KEY,
        'timeFrame': 'day',
        'includeIngredients': liked,
        'excludeIngredients': disliked
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return "Erro ao gerar plano alimentar", 500

    plan = response.json()
    recipe_ids = [str(meal['id']) for meal in plan['meals']]

    detailed_recipes = []
    shopping_list = {}

    for recipe_id in recipe_ids:
        detail_url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
        detail_res = requests.get(detail_url, params={'apiKey': API_KEY})
        if detail_res.status_code == 200:
            recipe = detail_res.json()
            detailed_recipes.append(recipe)
            for ing in recipe.get('extendedIngredients', []):
                name = ing['name']
                amount = f"{ing['amount']} {ing['unit']}".strip()
                shopping_list.setdefault(name, []).append(amount)

    return render_template('view_recipe.html',
                           recipe=detailed_recipes[0],
                           plan=plan,
                           recipes=detailed_recipes,
                           shopping_list=shopping_list,
                           search_query='',
                           liked_ingredients=liked,
                           disliked_ingredients=disliked)

@app.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
def view_recipe(recipe_id):
    search_query = request.args.get('search_query', '')
    
    # Carregar receita original da API
    url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
    response = requests.get(url, params={'apiKey': API_KEY})
    if response.status_code != 200:
        return "Recipe not found", 404
    recipe = response.json()

    # Comentários armazenados na base
    comments = list(comments_col.find({'recipe_id': recipe_id}))
    
    # Processar POST para adicionar comentários ou editar ingredientes
    if request.method == 'POST':
        if 'comment' in request.form:
            comment_text = request.form['comment'].strip()
            if comment_text:
                comments_col.insert_one({
                    'recipe_id': recipe_id,
                    'comment': comment_text
                })
                return redirect(url_for('view_recipe', recipe_id=recipe_id, search_query=search_query))

        elif 'update_ingredients' in request.form:
            # Receber ingredientes modificados via textarea JSON ou outra forma
            import json
            modified_ingredients_str = request.form.get('modified_ingredients', '')
            try:
                modified_ingredients = json.loads(modified_ingredients_str)
                # Substituir lista original por modificada (no lado do template)
                recipe['extendedIngredients'] = modified_ingredients
            except Exception as e:
                return f"Erro ao modificar ingredientes: {str(e)}", 400

    # Gerar lista de compras baseada nos ingredientes atuais da receita
    shopping_list = {}
    for ing in recipe.get('extendedIngredients', []):
        name = ing.get('name', '')
        amount = f"{ing.get('amount', '')} {ing.get('unit', '')}".strip()
        shopping_list.setdefault(name, []).append(amount)

    return render_template('view_recipe_edit.html',
                           recipe=recipe,
                           search_query=search_query,
                           comments=comments,
                           shopping_list=shopping_list)
    
if __name__ == '__main__':
    app.run(debug=True)
