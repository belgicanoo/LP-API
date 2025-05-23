from flask import Flask, render_template, request, redirect, url_for
import requests
from urllib.parse import unquote

app = Flask(__name__)

API_KEY = '102e440d05e14a75b434d6de15670598'

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

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    search_query = request.args.get('search_query', '')
    url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
    response = requests.get(url, params={'apiKey': API_KEY})
    if response.status_code == 200:
        recipe = response.json()
        return render_template('view_recipe.html', recipe=recipe, search_query=search_query)
    return "Recipe not found", 404

if __name__ == '__main__':
    app.run(debug=True)
