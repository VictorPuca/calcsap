import tkinter as tk
from tkinter import ttk, messagebox
import requests

camadas = []
ESCALA_ALTURA = 30
CORES = ["#c2b280", "#d9d9d9", "#a9a9a9", "#7f7f7f", "#9999cc", "#cccc99", "#c49a6c", "#e6ccb2"]

# Função para enviar os dados
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

        camada = {
            "Espessura": espessura,
            "Peso": peso,
            "NSPT": nspt,
            "Descrição": descricao
        }

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
    if not selecionado:
        messagebox.showinfo("Editar", "Selecione uma camada para editar.")
        return

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
    if not selecionado:
        messagebox.showinfo("Duplicar", "Selecione uma camada para duplicar.")
        return

    index = tabela.index(selecionado[0])
    camada = camadas[index].copy()
    camadas.insert(index + 1, camada)
    tabela.insert("", index + 1, values=(camada["Espessura"], camada["Peso"], camada["NSPT"], camada["Descrição"]))
    desenhar_perfil()

def excluir():
    selecionado = tabela.selection()
    if not selecionado:
        messagebox.showinfo("Excluir", "Selecione uma camada para excluir.")
        return

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

        canvas.create_rectangle(50, y_atual, canvas_largura, y_atual + altura_px, fill=cor_atual, outline="")
        canvas.create_line(50, y_atual, 50, y_atual + altura_px, fill="black")
        canvas.create_line(canvas_largura, y_atual, canvas_largura, y_atual + altura_px, fill="black")
        canvas.create_line(50, y_atual, canvas_largura, y_atual, fill="black")

        proxima = camadas[i + 1] if i + 1 < len(camadas) else None
        if not proxima or not (
            camada["Descrição"].strip().lower() == proxima["Descrição"].strip().lower()
            and camada["Peso"] == proxima["Peso"]
        ):
            canvas.create_line(50, y_atual + altura_px, canvas_largura, y_atual + altura_px, fill="black")

        if not (mesma_desc and mesmo_peso):
            texto = f'{camada["Descrição"]}\nγ: {camada["Peso"]} kN/m³'
            canvas.create_text((canvas_largura + 50) / 2, y_atual + altura_px / 2,
                               text=texto, font=("Arial", 8), fill="black", justify="center")

        canvas.create_text(30, y_atual + altura_px / 2,
                           text=f"{profundidade_acumulada:.2f} m", font=("Arial", 8), fill="black")

        canvas.create_text(canvas_largura - 10, y_atual + altura_px - 10,
                           text=f"NSPT: {camada['NSPT']}", font=("Arial", 8), fill="black", anchor="e")

        y_atual += altura_px
        profundidade_acumulada += camada["Espessura"]
        ultima_desc = camada["Descrição"]
        ultimo_peso = camada["Peso"]

    # Desenhar linha do nível d'água
    try:
        nivel_agua = float(var_nivel_agua.get())
        y_na = nivel_agua * ESCALA_ALTURA
        profundidade_total = sum(c["Espessura"] for c in camadas)
        altura_canvas = profundidade_total * ESCALA_ALTURA

        if 0 <= y_na <= altura_canvas:
            canvas.create_line(50, y_na, canvas_largura, y_na, fill="blue", dash=(4, 2), width=2)
            canvas.create_text(52.5, y_na - 5, text="N.A", fill="blue", anchor="sw", font=("Arial", 9, "bold"))
    except Exception as e:
        print("Erro ao desenhar N.A:", e)

# Interface
janela = tk.Tk()
janela.title("FundCalc [v1.0]")
janela.geometry("1000x550")
janela.configure(bg="#f0f0f0")

frame_entrada = ttk.Frame(janela)
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
entry_nivel_agua = criar_linha_input("Profundidade do nível d'água (m):", var_nivel_agua)

botoes_frame = ttk.Frame(frame_entrada)
botoes_frame.pack(pady=10, fill="x")

ttk.Button(botoes_frame, text="Adicionar", command=adicionar).pack(fill="x", pady=2)
ttk.Button(botoes_frame, text="Editar", command=editar).pack(fill="x", pady=2)
ttk.Button(botoes_frame, text="Duplicar", command=duplicar).pack(fill="x", pady=2)
ttk.Button(botoes_frame, text="Excluir", command=excluir).pack(fill="x", pady=2)
ttk.Button(botoes_frame, text="Limpar Tudo", command=limpar_tudo).pack(fill="x", pady=2)
ttk.Button(botoes_frame, text="Salvar Dados do Perfil de Sondagem", command=enviar_camadas_para_api).pack(fill="x", pady=2)

tabela = ttk.Treeview(frame_entrada, columns=("esp", "peso", "nspt", "desc"), show="headings", height=10)
for col, name in zip(("esp", "peso", "nspt", "desc"), ["Espessura (m)", "γ (kN/m³)", "NSPT", "Descrição"]):
    tabela.heading(col, text=name)
    tabela.column(col, anchor="center", width=120 if col != "desc" else 160)
tabela.pack(pady=10, fill="x")

frame_canvas = ttk.Frame(janela)
frame_canvas.pack(side="right", fill="both", expand=True, padx=10, pady=10)

tk.Label(frame_canvas, text="Perfil Geotécnico", font=("Arial", 12, "bold")).pack()
canvas = tk.Canvas(frame_canvas, bg="white")
canvas.pack(fill="both", expand=True)
canvas.bind("<Configure>", desenhar_perfil)

# Atualiza o canvas ao alterar o nível d’água
var_nivel_agua.trace_add("write", lambda *args: desenhar_perfil())

janela.mainloop()
