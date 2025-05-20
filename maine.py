import requests
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import os

API_KEY = "102e440d05e14a75b434d6de15670598"
BASE_URL = "https://api.spoonacular.com"

receitas_atuais = []

def gerar_plano_diario(desejados, evitar, calorias):
    url = f"{BASE_URL}/mealplanner/generate"
    params = {
        "apiKey": API_KEY,
        "timeFrame": "day",
        "targetCalories": calorias,
        "includeIngredients": ",".join(desejados),
        "excludeIngredients": ",".join(evitar)
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def obter_detalhes_receita(meal_id):
    url = f"{BASE_URL}/recipes/{meal_id}/information"
    params = {"apiKey": API_KEY, "includeNutrition": False}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

def gerar_lista_de_compras(refeicoes, porcoes):
    ingredientes = {}
    for meal in refeicoes:
        detalhes = obter_detalhes_receita(meal['id'])
        for ingrediente in detalhes['extendedIngredients']:
            nome = ingrediente["name"]
            quantidade = ingrediente["amount"] * porcoes
            unidade = ingrediente["unit"]
            if nome not in ingredientes:
                ingredientes[nome] = {"amount": quantidade, "unit": unidade}
            else:
                ingredientes[nome]["amount"] += quantidade
    return ingredientes

def guardar_comentario(nome_receita, comentario):
    ficheiro = f"comentarios_{nome_receita}.txt"
    with open(ficheiro, "a", encoding="utf-8") as f:
        f.write(f"{comentario.strip()}\n")

def carregar_comentarios(nome_receita):
    ficheiro = f"comentarios_{nome_receita}.txt"
    comentarios_output.config(state=tk.NORMAL)
    comentarios_output.delete(1.0, tk.END)
    comentarios_output.insert(tk.END, f"💬 Comentários para '{nome_receita}':\n\n")
    if os.path.exists(ficheiro):
        with open(ficheiro, "r", encoding="utf-8") as f:
            for linha in f:
                comentarios_output.insert(tk.END, f"- {linha}")
    else:
        comentarios_output.insert(tk.END, "Sem comentários ainda.\n")
    comentarios_output.config(state=tk.DISABLED)

def atualizar_receitas_dropdown():
    receita_menu['values'] = receitas_atuais
    if receitas_atuais:
        receita_menu.current(0)
        carregar_comentarios(receitas_atuais[0])

def ao_mudar_receita(event=None):
    selecionada = receita_var.get()
    if selecionada:
        carregar_comentarios(selecionada)

def publicar_comentario():
    comentario = comentario_entry.get("1.0", tk.END).strip()
    nome_receita = receita_var.get()
    if not nome_receita:
        messagebox.showwarning("Aviso", "Seleciona uma receita para comentar.")
        return
    if comentario:
        guardar_comentario(nome_receita, comentario)
        carregar_comentarios(nome_receita)
        comentario_entry.delete("1.0", tk.END)
    else:
        messagebox.showwarning("Aviso", "Escreve um comentário antes de enviar.")

def gerar():
    global receitas_atuais
    desejados = incluir_entry.get().strip().lower().split(",")
    evitar = evitar_entry.get().strip().lower().split(",")
    calorias_input = calorias_entry.get().strip()
    porcoes_input = porcoes_entry.get().strip()

    try:
        calorias = int(calorias_input)
        porcoes = int(porcoes_input)
        if porcoes < 1:
            raise ValueError
    except ValueError:
        messagebox.showerror("Erro", "Digite valores válidos para calorias e porções.")
        return

    try:
        plano = gerar_plano_diario(desejados, evitar, calorias)
        refeicoes = plano['meals']
        receitas_atuais = []

        plano_output.config(state=tk.NORMAL)
        plano_output.delete(1.0, tk.END)
        plano_output.insert(tk.END, f"🍽 Plano Alimentar do Dia (para {porcoes} pessoa(s)):\n")

        for meal in refeicoes:
            detalhes = obter_detalhes_receita(meal['id'])
            nome_receita = meal['title']
            receitas_atuais.append(nome_receita)

            plano_output.insert(tk.END, f"\n🍲 {nome_receita}\n")
            plano_output.insert(tk.END, f"⏱ Tempo de preparo: {detalhes.get('readyInMinutes')} minutos\n")
            plano_output.insert(tk.END, f"📋 Ingredientes (para {porcoes} porção(ões)):\n")
            for ing in detalhes['extendedIngredients']:
                total = ing['amount'] * porcoes
                plano_output.insert(tk.END, f"  - {total:.2f} {ing['unit']} {ing['name']}\n")
            plano_output.insert(tk.END, f"\n📖 Instruções:\n{detalhes.get('instructions') or 'Sem instruções disponíveis.'}\n")
            plano_output.insert(tk.END, "-"*50 + "\n\n")

        atualizar_receitas_dropdown()

        lista = gerar_lista_de_compras(refeicoes, porcoes)
        compras_output.config(state=tk.NORMAL)
        compras_output.delete(1.0, tk.END)
        compras_output.insert(tk.END, f"🛒 Lista de Compras para {porcoes} pessoa(s):\n")
        for item, info in lista.items():
            compras_output.insert(tk.END, f" - {item.title()}: {info['amount']:.2f} {info['unit']}\n")

        plano_output.config(state=tk.DISABLED)
        compras_output.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("Erro", str(e))

# 🖥 Interface Gráfica
app = tk.Tk()
app.title("Plano Alimentar Diário Personalizado")
app.geometry("900x850")

frame_inputs = tk.Frame(app)
frame_inputs.pack(pady=10)

tk.Label(frame_inputs, text="Ingredientes desejados (vírgula):").grid(row=0, column=0, sticky="e", padx=5)
incluir_entry = tk.Entry(frame_inputs, width=40)
incluir_entry.grid(row=0, column=1, padx=5)

tk.Label(frame_inputs, text="Ingredientes a evitar (vírgula):").grid(row=1, column=0, sticky="e", padx=5)
evitar_entry = tk.Entry(frame_inputs, width=40)
evitar_entry.grid(row=1, column=1, padx=5)

tk.Label(frame_inputs, text="Calorias por dia:").grid(row=2, column=0, sticky="e", padx=5)
calorias_entry = tk.Entry(frame_inputs, width=10)
calorias_entry.insert(0, "2000")
calorias_entry.grid(row=2, column=1, sticky="w", padx=5)

tk.Label(frame_inputs, text="Número de porções:").grid(row=3, column=0, sticky="e", padx=5)
porcoes_entry = tk.Entry(frame_inputs, width=10)
porcoes_entry.insert(0, "1")
porcoes_entry.grid(row=3, column=1, sticky="w", padx=5)

tk.Button(frame_inputs, text="Gerar Plano do Dia", command=gerar).grid(row=4, columnspan=2, pady=10)

plano_output = scrolledtext.ScrolledText(app, height=20, wrap=tk.WORD)
plano_output.pack(fill="both", expand=True, padx=10, pady=5)

compras_output = scrolledtext.ScrolledText(app, height=8, wrap=tk.WORD)
compras_output.pack(fill="both", expand=True, padx=10, pady=5)

tk.Label(app, text="Seleciona uma receita para comentar:").pack()
receita_var = tk.StringVar()
receita_menu = ttk.Combobox(app, textvariable=receita_var, state="readonly", width=60)
receita_menu.pack(pady=5)
receita_menu.bind("<<ComboboxSelected>>", ao_mudar_receita)

tk.Label(app, text="Escreve o teu comentário:").pack()
comentario_entry = tk.Text(app, height=3, width=80)
comentario_entry.pack(padx=10)

tk.Button(app, text="Publicar Comentário", command=publicar_comentario).pack(pady=5)

comentarios_output = scrolledtext.ScrolledText(app, height=8, wrap=tk.WORD, state=tk.DISABLED)
comentarios_output.pack(fill="both", expand=True, padx=10, pady=5)

app.mainloop()