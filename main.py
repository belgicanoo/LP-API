import requests
from flask import Flask, render_template, request
from urllib.parse import unquote
import spoonacular as sp
#Primeiro criar a funcionalidade para a pessoa dizer o que quer

#Criação da applicação flask
app = Flask(__name__)

#Chave e a url da API
API_KEY = "102e440d05e14a75b434d6de15670598"
BASE_URL = "https://api.spoonacular.com"

#Define the route for the home button
@app.route('/home', methods=['GET'])
def home():
    #Render the main page with empty recipe list and search query
    return render_template('index.html', recipes=[], search_query='')

#Define the main route for the app
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        #If a form is submitted
        query = request.form.get('search_query','')
        #Perform a search for recipe with the given query
        recipes = search_recipes(query)
        #Render the main page with the search results and the search query
        return render_template('index.html', recipes=recipes, search_query=query)

#If it's a GET request or no form submitted
search_query = request.args.get('search_query', '')
decoded_search_query = unquote(search_query)
#Perform a search for recipes with the decoded search query
recipes = search_recipes(decoded_search_query)
#Render the main app 
return render_template('index.html', recipes=recipes, search_query=decoded_search_query)

#Function to search for recipes based on the provided query
def search_recipes(query):
    url = f'https://api.spoonacular.com/recipes/complexSearch'
    params = {
        'apiKey': API_KEY,
        'query': query,
        'number': 10,
        'instructionsRequired': True,
        'addRecipeInformation': True,
        'fillIngredients': True,
    }

    #Send a GET request to the Spoonacular APU with the query parameters
    response = requests.get(url, params=params)
    # If the API call is sucessful
    if response.status_code == 200:
        #Parse the API response as JSON Data
        data = response.json()
        #Return the list of recupe results
        return data['results']
    #It not sucessfull
    return []

#Route to view a specific recipe with a given recipe ID
@app.route('/recipe/<int:recippe_id>')
def view_recipe(recipe_id):
    #Get the search query from the URL query parameters
    search_query = request.args.get('search_query', '')
    
