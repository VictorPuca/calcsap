import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from scipy.optimize import fsolve

# ------------------ VARIÁVEIS GLOBAIS ------------------ #
camadas = []
ESCALA_ALTURA = 30
CORES = ["#c2b280", "#d9d9d9", "#a9a9a9", "#7f7f7f", "#9999cc", "#cccc99", "#c49a6c", "#e6ccb2"]
dados_json = None
ARQUIVO_DB = "camadas_db.json"

# ------------------ FUNÇÕES GERAIS ------------------ #
def carregar_json_inicial():
    global dados_json
    try:
        with open(ARQUIVO_DB, "r") as f:
            dados_json = json.load(f)
    except:
        dados_json = {"camadas": [], "nivel_agua": None}

# ------------------ ABA 1: PERFIL GEOTÉCNICO ------------------ #
def enviar_camadas_para_api():
    url = "http://127.0.0.1:8000/camadas"
    try:
        dados = {
            "camadas": camadas,
            "nivel_agua": float(var_nivel_agua.get()) if var_nivel_agua.get() else None
        }
        resposta = requests.post(url, json=dados)
        resposta.raise_for_status()
        messagebox.showinfo("Sucesso", "Perfil de Sondagem salvo com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro ao enviar dados", f"Não foi possível enviar os dados para a API.\n\n{e}")

def adicionar():
    try:
        espessura = float(entry_espessura.get())
        peso = float(entry_peso.get())
        nspt = int(entry_nspt.get())
        descricao = entry_descricao.get()

        camada = {"Espessura": espessura, "Peso": peso, "NSPT": nspt, "Descrição": descricao}

        selecionado = tabela.selection()
        if selecionado:
            index = tabela.index(selecionado[0])
            camadas[index] = camada
            tabela.item(selecionado, values=(espessura, peso, nspt, descricao))
        else:
            camadas.append(camada)
            tabela.insert("", "end", values=(espessura, peso, nspt, descricao))

        desenhar_perfil()
        limpar_entradas()

    except Exception as e:
        messagebox.showerror("Erro", f"Verifique os dados inseridos.\n\n{e}")

def editar():
    selecionado = tabela.selection()
    if not selecionado: return
    index = tabela.index(selecionado[0])
    camada = camadas[index]

    entry_espessura.delete(0, tk.END)
    entry_espessura.insert(0, camada["Espessura"])

    entry_peso.delete(0, tk.END)
    entry_peso.insert(0, camada["Peso"])

    entry_nspt.delete(0, tk.END)
    entry_nspt.insert(0, camada["NSPT"])

    entry_descricao.delete(0, tk.END)
    entry_descricao.insert(0, camada["Descrição"])

def duplicar():
    selecionado = tabela.selection()
    if not selecionado: return
    index = tabela.index(selecionado[0])
    camada = camadas[index].copy()
    camadas.insert(index + 1, camada)
    tabela.insert("", index + 1, values=(camada["Espessura"], camada["Peso"], camada["NSPT"], camada["Descrição"]))
    desenhar_perfil()

def excluir():
    selecionado = tabela.selection()
    if not selecionado: return
    index = tabela.index(selecionado[0])
    del camadas[index]
    tabela.delete(selecionado[0])
    desenhar_perfil()

def limpar_entradas():
    entry_espessura.delete(0, tk.END)
    entry_peso.delete(0, tk.END)
    entry_nspt.delete(0, tk.END)
    entry_descricao.delete(0, tk.END)
    tabela.selection_remove(tabela.selection())

def limpar_tudo():
    if messagebox.askyesno("Limpar Tudo", "Deseja remover todas as camadas?"):
        camadas.clear()
        tabela.delete(*tabela.get_children())
        desenhar_perfil()

def desenhar_perfil(event=None):
    canvas.delete("all")
    canvas_largura = canvas.winfo_width()
    y_atual = 0
    ultima_desc = None
    ultimo_peso = None
    cor_atual = CORES[0]
    cor_index = 0
    profundidade_acumulada = 0

    for i, camada in enumerate(camadas):
        altura_px = camada["Espessura"] * ESCALA_ALTURA
        mesma_desc = camada["Descrição"].strip().lower() == (ultima_desc or "").strip().lower()
        mesmo_peso = camada["Peso"] == ultimo_peso

        if not (mesma_desc and mesmo_peso):
            cor_atual = CORES[cor_index % len(CORES)]
            cor_index += 1

        canvas.create_rectangle(50, y_atual, canvas_largura, y_atual + altura_px, fill=cor_atual, outline="black")
        canvas.create_text((canvas_largura + 50) / 2, y_atual + altura_px / 2,
                           text=f'{camada["Descrição"]}\nγ: {camada["Peso"]} kN/m³', font=("Arial", 8))

        canvas.create_text(30, y_atual + altura_px / 2, text=f"{profundidade_acumulada:.2f} m", font=("Arial", 8))
        canvas.create_text(canvas_largura - 10, y_atual + altura_px - 10,
                           text=f"NSPT: {camada['NSPT']}", font=("Arial", 8), anchor="e")

        y_atual += altura_px
        profundidade_acumulada += camada["Espessura"]
        ultima_desc = camada["Descrição"]
        ultimo_peso = camada["Peso"]

    try:
        nivel_agua = float(var_nivel_agua.get())
        y_na = nivel_agua * ESCALA_ALTURA
        if 0 <= y_na <= y_atual:
            canvas.create_line(50, y_na, canvas_largura, y_na, fill="blue", dash=(4, 2), width=2)
            canvas.create_text(52.5, y_na - 5, text="N.A", fill="blue", anchor="sw", font=("Arial", 9, "bold"))
    except:
        pass

# ------------------ ABA 2: CÁLCULO DE SAPATA ------------------ #
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

def calcular_gamma2(camadas, h, nivel_agua):
    profundidade = 0.0
    camada_abaixo = None
    for camada in camadas:
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
    topo_camada = profundidade
    base_camada = topo_camada + esp_camada

    if nivel_agua <= topo_camada:
        return γ_nat
    elif nivel_agua >= base_camada:
        return γ_nat - γ_agua
    else:
        altura_sub = base_camada - nivel_agua
        altura_nat = nivel_agua - topo_camada
        return ((γ_nat - γ_agua) * altura_sub + γ_nat * altura_nat) / esp_camada

def carregar_json_sapata(entries):
    if dados_json is None:
        return

    try:
        cam = dados_json["camadas"]
        na = dados_json["nivel_agua"]
        h = float(entries["h"].get())

        q_calc = calcular_sobrecarga(cam, h, na)
        g2_calc = calcular_gamma2(cam, h, na)

        entries["q"].delete(0, tk.END)
        entries["q"].insert(0, f"{q_calc:.3f}")
        entries["g2"].delete(0, tk.END)
        entries["g2"].insert(0, f"{g2_calc:.3f}")

    except Exception as e:
        messagebox.showerror("Erro", str(e))

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
        r = float(entries["r"].get()) if "r" in entries and entries["r"].get() else 1

        if tipo == "quadrada":
            sc, sq, sγ = 1.3, 1.3, 0.6
        elif tipo == "retangular":
            sc = 1 + 0.3 * r
            sq = 1 + 0.3 * r
            sγ = 1 - 0.4 * r
        elif tipo == "corrida": # Sapata corrida (B é a largura, L é infinito)
            sc = sq = sγ = 1
        else: # Default para caso algo dê errado
            sc = sq = sγ = 1

        def func(B):
            pr = (sc / cs) * c * nc + (sq / cs) * q * nq + (sγ / cs) * 0.5 * γ2 * B * nγ
            if tipo == "quadrada":
                area = B**2
            elif tipo == "corrida":
                area = B * 1.0 # Considera L=1 para sapata corrida para calcular Pr por metro linear
            else: # tipo == "retangular"
                area = B * (1 / r) # B é a largura, L = B/r

            return area * pr - P

        B = fsolve(func, 0.5)[0]
        resultado_vars[0].set(f"Largura (B): {B:.4f} m")

        if tipo == "quadrada":
            resultado_vars[1].set(f"Comprimento (L): {B:.4f} m")
        elif tipo == "retangular":
            L = B * (1 / r)
            resultado_vars[1].set(f"Comprimento (L): {L:.4f} m")
        else: # tipo == "corrida"
            resultado_vars[1].set("Sapata Corrida (Cálculo por metro linear)")

    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira valores numéricos válidos em todos os campos.")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro no cálculo: {str(e)}")


def configurar_aba_sapata(notebook):
    aba = ttk.Frame(notebook)
    notebook.add(aba, text="Cálculo de Sapata")
    frame = ttk.Frame(aba, padding=10)
    frame.pack(expand=True, fill="both")

    # Dropdown para seleção do tipo de sapata
    ttk.Label(frame, text="Tipo de Sapata:").grid(row=0, column=0, sticky="w", pady=5)
    
    # Adicionando um StringVar para o Combobox
    global var_tipo_sapata
    var_tipo_sapata = tk.StringVar(janela)
    var_tipo_sapata.set("quadrada") # Valor inicial

    # Criando o Combobox e associando a função de atualização
    combo_sapata = ttk.Combobox(frame, textvariable=var_tipo_sapata,
                                values=["quadrada", "retangular", "corrida"], state="readonly")
    combo_sapata.grid(row=0, column=1, pady=5, sticky="ew")
    combo_sapata.bind("<<ComboboxSelected>>", lambda event: atualizar_campos_sapata())

    # Frame para os campos de entrada (será atualizado dinamicamente)
    global campos_frame
    campos_frame = ttk.Frame(frame)
    campos_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=10)
    
    # Dicionário para armazenar as variáveis e entradas dos campos
    global entries_sapata
    entries_sapata = {}
    
    global resultado_var_b, resultado_var_l
    resultado_var_b = tk.StringVar()
    resultado_var_l = tk.StringVar()

    ttk.Button(frame, text="Importar Dados do Perfil", command=lambda: carregar_json_sapata(entries_sapata)).grid(row=2, column=0, pady=5, sticky="w")
    ttk.Button(frame, text="Calcular", command=lambda: calcular_sapata(var_tipo_sapata.get(), entries_sapata, [resultado_var_b, resultado_var_l])).grid(row=2, column=1, pady=5, sticky="e")

    ttk.Label(frame, textvariable=resultado_var_b).grid(row=3, column=0, columnspan=2, sticky="w", pady=2)
    ttk.Label(frame, textvariable=resultado_var_l).grid(row=4, column=0, columnspan=2, sticky="w", pady=2)

    frame.columnconfigure(1, weight=1)
    
    # Inicializa os campos
    atualizar_campos_sapata()

def atualizar_campos_sapata():
    # Limpa todos os widgets do frame de campos
    for widget in campos_frame.winfo_children():
        widget.destroy()
    
    # Define os campos com base no tipo de sapata selecionado
    tipo = var_tipo_sapata.get()
    
    # Campos comuns a todos os tipos de sapata
    campos_base = [
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
    
    # Adiciona o campo 'r' se for retangular ou corrida
    campos_atuais = campos_base[:]
    if tipo == "retangular":
        campos_atuais.insert(1, ("Razão B/L (B<L):", "r")) # Insere 'r' após 'h'
        
    # Recria os campos
    for i, (label_text, key) in enumerate(campos_atuais):
        ttk.Label(campos_frame, text=label_text).grid(row=i, column=0, sticky="w")
        ent = ttk.Entry(campos_frame)
        ent.grid(row=i, column=1, pady=2, sticky="ew")
        entries_sapata[key] = ent # Armazena a referência para a entrada

    # Limpa resultados anteriores quando o tipo de sapata muda
    resultado_var_b.set("")
    resultado_var_l.set("")
    
    # Define a configuração de coluna para o campo_frame
    campos_frame.columnconfigure(1, weight=1)


# ------------------ INICIALIZAÇÃO ------------------ #
janela = tk.Tk()
janela.title("FundCalc [v1.0]")
janela.geometry("1100x600")

notebook = ttk.Notebook(janela)
notebook.pack(fill="both", expand=True)

# Aba: Perfil Geotécnico
aba_perfil = ttk.Frame(notebook)
notebook.add(aba_perfil, text="Perfil Geotécnico")

# Interface do perfil geotécnico
frame_entrada = ttk.Frame(aba_perfil)
frame_entrada.pack(side="left", padx=10, pady=10, fill="y")

form_frame = ttk.LabelFrame(frame_entrada, text="Nova Camada")
form_frame.pack(padx=5, pady=5, fill="x")

def criar_linha_input(label_text, entry_var):
    row = ttk.Frame(form_frame)
    row.pack(fill="x", pady=2)
    ttk.Label(row, text=label_text, width=20).pack(side="left")
    entry = tk.Entry(row, textvariable=entry_var)
    entry.pack(side="right", expand=True, fill="x")
    return entry

var_espessura = tk.StringVar()
var_peso = tk.StringVar()
var_nspt = tk.StringVar()
var_descricao = tk.StringVar()
var_nivel_agua = tk.StringVar()

entry_espessura = criar_linha_input("Espessura (m):", var_espessura)
entry_peso = criar_linha_input("Peso específico (tf/m³):", var_peso)
entry_nspt = criar_linha_input("NSPT:", var_nspt)
entry_descricao = criar_linha_input("Descrição do solo:", var_descricao)
entry_nivel_agua = criar_linha_input("Profundidade do N.A:", var_nivel_agua)

botoes_frame = ttk.Frame(frame_entrada)
botoes_frame.pack(pady=10, fill="x")

ttk.Button(botoes_frame, text="Adicionar", command=adicionar).pack(fill="x", pady=2)
ttk.Button(botoes_frame, text="Editar", command=editar).pack(fill="x", pady=2)
ttk.Button(botoes_frame, text="Duplicar", command=duplicar).pack(fill="x", pady=2)
ttk.Button(botoes_frame, text="Excluir", command=excluir).pack(fill="x", pady=2)
ttk.Button(botoes_frame, text="Limpar Tudo", command=limpar_tudo).pack(fill="x", pady=2)
ttk.Button(botoes_frame, text="Salvar Dados", command=enviar_camadas_para_api).pack(fill="x", pady=2)

tabela = ttk.Treeview(frame_entrada, columns=("esp", "peso", "nspt", "desc"), show="headings", height=10)
for col, name in zip(("esp", "peso", "nspt", "desc"), ["Espessura (m)", "γ (kN/m³)", "NSPT", "Descrição"]):
    tabela.heading(col, text=name)
    tabela.column(col, anchor="center", width=120 if col != "desc" else 160)
tabela.pack(pady=10, fill="x")

frame_canvas = ttk.Frame(aba_perfil)
frame_canvas.pack(side="right", fill="both", expand=True, padx=10, pady=10)
tk.Label(frame_canvas, text="Perfil Geotécnico", font=("Arial", 12, "bold")).pack()
canvas = tk.Canvas(frame_canvas, bg="white")
canvas.pack(fill="both", expand=True)
canvas.bind("<Configure>", desenhar_perfil)
var_nivel_agua.trace_add("write", lambda *args: desenhar_perfil())

# Aba: Cálculo de Sapata (única)
configurar_aba_sapata(notebook)

carregar_json_inicial()
janela.mainloop()