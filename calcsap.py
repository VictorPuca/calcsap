import tkinter as tk
from tkinter import ttk, messagebox
from scipy.optimize import fsolve
import json

# Variável global para armazenar os dados do JSON
dados_json = None

# Função para calcular sobrecarga q
def calcular_sobrecarga(camadas, h, nivel_agua):
    q = 0.0
    profundidade = 0.0
    for camada in camadas:
        esp = camada["Espessura"]
        γ = camada["Peso"]

        if profundidade >= h:
            break

        altura_util = min(esp, h - profundidade)
        topo = profundidade
        base = profundidade + altura_util

        if nivel_agua >= base:
            q += γ * altura_util
        elif nivel_agua <= topo:
            γ_sub = γ - 1.0
            q += γ_sub * altura_util
        else:
            altura_acima = nivel_agua - topo
            altura_abaixo = base - nivel_agua
            γ_sub = γ - 1.0
            q += γ * altura_acima + γ_sub * altura_abaixo

        profundidade += esp
    return q

# Função para calcular γ2
def calcular_gamma2(camadas, h, nivel_agua):
    profundidade = 0.0
    camada_abaixo = None

    for i, camada in enumerate(camadas):
        esp = camada["Espessura"]
        topo = profundidade
        base = profundidade + esp

        if h > topo and h <= base:
            camada_abaixo = camada
            break
        profundidade += esp

    if camada_abaixo is None:
        camada_abaixo = camadas[-1]

    esp_camada = camada_abaixo["Espessura"]
    γ_nat = camada_abaixo["Peso"]
    γ_agua = 1.0

    profundidade = 0.0
    for camada in camadas:
        if camada == camada_abaixo:
            break
        profundidade += camada["Espessura"]

    topo_camada = profundidade
    base_camada = topo_camada + esp_camada

    if nivel_agua <= topo_camada:
        γ2 = γ_nat
    elif nivel_agua >= base_camada:
        γ2 = γ_nat - γ_agua
    else:
        altura_submersa = base_camada - nivel_agua
        altura_natural = nivel_agua - topo_camada
        γ_sub = γ_nat - γ_agua
        γ2 = (γ_sub * altura_submersa + γ_nat * altura_natural) / esp_camada

    return γ2

# Função para calcular sapata
def calcular_sapata(tipo, entries, resultado_vars):
    try:
        P = float(entries["p"].get())
        h = float(entries["h"].get())
        nc = float(entries["nc"].get())
        nq = float(entries["nq"].get())
        nγ = float(entries["ng"].get())
        c = float(entries["c"].get())
        q = float(entries["q"].get())
        γ2 = float(entries["g2"].get())
        cs = float(entries["cs"].get())
        r = float(entries["r"].get()) if "r" in entries else 1

        if tipo == "quadrada":
            sc, sq, sγ = 1.3, 1.3, 0.6
        elif tipo == "retangular":
            sc = 1 + 0.3 * r
            sq = 1 + 0.3 * r
            sγ = 1 - 0.4 * r
        elif tipo == "corrida":
            sc, sq, sγ = 1, 1, 1

        def func(B):
            pr = (sc / cs) * c * nc + (sq / cs) * q * nq + (sγ / cs) * 0.5 * γ2 * B * nγ
            area = B**2 if tipo == "quadrada" else (1 / r) * B
            return area * pr - P

        B = fsolve(func, 0.5)[0]

        resultado_vars[0].set(f"Largura da sapata: {B:.4f} m")

        if tipo != "quadrada":
            L = B * (1 / r)
            resultado_vars[1].set(f"Comprimento da sapata: {L:.4f} m")

    except Exception as e:
        messagebox.showerror("Erro", f"Verifique os dados inseridos.\n\nDetalhes: {e}")

# Carregamento inicial do JSON
def carregar_json_inicial():
    global dados_json
    try:
        with open("camadas_db.json", "r") as f:
            dados_json = json.load(f)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar 'camadas_db.json'.\n\nDetalhes: {e}")

# Usar dados carregados para preencher q e γ2
def carregar_json(entries):
    global dados_json
    if dados_json is None:
        messagebox.showwarning("Aviso", "Dados JSON ainda não foram carregados.")
        return

    try:
        camadas = dados_json["camadas"]
        nivel_agua = dados_json["nivel_agua"]

        h_str = entries["h"].get()
        if not h_str:
            messagebox.showwarning("Aviso", "Preencha o campo 'Altura de assentamento (h)' antes.")
            return

        h = float(h_str)

        q_calc = calcular_sobrecarga(camadas, h, nivel_agua)
        entries["q"].delete(0, tk.END)
        entries["q"].insert(0, f"{q_calc:.3f}")

        γ2_calc = calcular_gamma2(camadas, h, nivel_agua)
        entries["g2"].delete(0, tk.END)
        entries["g2"].insert(0, f"{γ2_calc:.3f}")

        messagebox.showinfo("Sucesso", "Campos preenchidos com q e γ2 calculados.")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar dados JSON.\n\nDetalhes: {e}")

# Criar interface de cada aba
def criar_aba(notebook, nome, campos, tipo):
    aba = ttk.Frame(notebook)
    notebook.add(aba, text=nome)

    frame = ttk.Frame(aba, padding=10)
    frame.pack(expand=True, fill="both")

    entries = {}
    for i, (label, key) in enumerate(campos):
        ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
        entry = ttk.Entry(frame)
        entry.grid(row=i, column=1, pady=5, padx=5, sticky="ew")
        entries[key] = entry

    resultado_var1 = tk.StringVar()
    resultado_var2 = tk.StringVar()

    ttk.Button(frame, text="Importar Dados do Perfil", command=lambda: carregar_json(entries)).grid(row=len(campos), column=0, pady=10, sticky="ew")
    ttk.Button(frame, text="Calcular", command=lambda: calcular_sapata(tipo, entries, [resultado_var1, resultado_var2])).grid(row=len(campos), column=1, pady=10, sticky="ew")

    ttk.Label(frame, textvariable=resultado_var1, font=("Arial", 10, "bold")).grid(row=len(campos)+1, column=0, columnspan=2, pady=5)
    if tipo != "quadrada":
        ttk.Label(frame, textvariable=resultado_var2, font=("Arial", 10, "bold")).grid(row=len(campos)+2, column=0, columnspan=2, pady=5)

    frame.columnconfigure(1, weight=1)

# Campos
campos_comuns = [
    ("Carga do pilar [tf]:", "p"),
    ("Altura de assentamento [m]:", "h"),
    ("Nc:", "nc"),
    ("Nq:", "nq"),
    ("Nγ:", "ng"),
    ("Coesão do solo [tf/m²]:", "c"),
    ("Sobrecarga [tf/m²]:", "q"),
    ("Peso específico γ2 [tf/m³]:", "g2"),
    ("Coef. de Segurança:", "cs")
]
campos_com_r = [("Razão B/L (B<L):", "r")] + campos_comuns

# Inicialização da janela
janela = tk.Tk()
janela.title("CalcSap")
janela.geometry("360x540")

notebook = ttk.Notebook(janela)
notebook.pack(expand=True, fill="both")

criar_aba(notebook, "Sapata Quadrada", campos_comuns, "quadrada")
criar_aba(notebook, "Sapata Retangular", campos_com_r, "retangular")
criar_aba(notebook, "Sapata Corrida", campos_com_r, "corrida")

carregar_json_inicial()
janela.mainloop()
