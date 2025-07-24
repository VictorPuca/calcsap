import tkinter as tk
from tkinter import ttk, messagebox
from scipy.optimize import fsolve

# Função base para cada cálculo
def calcular_sapata(tipo, entries, resultado_vars):
    try:
        P = float(entries["p"].get())
        nc = float(entries["nc"].get())
        nq = float(entries["nq"].get())
        nγ = float(entries["ng"].get())
        c = float(entries["c"].get())
        q = float(entries["q"].get())
        γ2 = float(entries["g2"].get())
        cs = float(entries["cs"].get())
        r = float(entries["r"].get()) if "r" in entries else 1

        # Coeficientes parciais
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
            area = B**2 if tipo == "quadrada" else (1/r)*B
            return area * pr - P

        B = fsolve(func, 0.5)[0]

        resultado_vars[0].set(f"Largura da sapata: {B:.4f} m")

        if tipo != "quadrada":
            L = B * (1/r)
            resultado_vars[1].set(f"Comprimento da sapata: {L:.4f} m")

    except Exception as e:
        messagebox.showerror("Erro", f"Verifique os dados inseridos.\n\nDetalhes: {e}")

# Criação da interface principal
janela = tk.Tk()
janela.title("CalcSap")
janela.geometry("300x500")

notebook = ttk.Notebook(janela)
notebook.pack(expand=True, fill="both")

# Campos comuns
campos_comuns = [
    ("Carga do pilar [tf]:", "p"),
    ("Nc:", "nc"),
    ("Nq:", "nq"),
    ("Nγ:", "ng"),
    ("Coesão do solo [tf/m²]:", "c"),
    ("Sobrecarga [tf/m²]:", "q"),
    ("Peso específico γ2 [tf/m³]:", "g2"),
    ("Coef. de Segurança:", "cs")
]

# Campos específicos com "r"
campos_com_r = [("Razão B/L (B<L):", "r")] + campos_comuns

# Função para criar aba
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

    ttk.Button(frame, text="Calcular", command=lambda: calcular_sapata(tipo, entries, [resultado_var1, resultado_var2])).grid(row=len(campos), column=0, columnspan=2, pady=10)

    ttk.Label(frame, textvariable=resultado_var1, font=("Arial", 10, "bold")).grid(row=len(campos)+1, column=0, columnspan=2, pady=5)
    if tipo != "quadrada":
        ttk.Label(frame, textvariable=resultado_var2, font=("Arial", 10, "bold")).grid(row=len(campos)+2, column=0, columnspan=2, pady=5)

    # Expansão automática
    frame.columnconfigure(1, weight=1)

# Criar abas
criar_aba(notebook, "Sapata Quadrada", campos_comuns, "quadrada")
criar_aba(notebook, "Sapata Retangular", campos_com_r, "retangular")
criar_aba(notebook, "Sapata Corrida", campos_com_r, "corrida")

janela.mainloop()
