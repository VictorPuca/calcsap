from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
import os

app = FastAPI()
ARQUIVO_DB = "camadas_db.json"

class Camada(BaseModel):
    Espessura: float
    Peso: float
    NSPT: int
    Descrição: str

def salvar_camadas(camadas: List[Camada]):
    with open(ARQUIVO_DB, "w", encoding="utf-8") as f:
        json.dump([c.dict() for c in camadas], f, ensure_ascii=False, indent=2)

def carregar_camadas() -> List[Camada]:
    if not os.path.exists(ARQUIVO_DB):
        return []
    with open(ARQUIVO_DB, "r", encoding="utf-8") as f:
        dados = json.load(f)
        return [Camada(**c) for c in dados]

@app.post("/camadas")
async def receber_camadas(camadas: List[Camada]):
    salvar_camadas(camadas)
    return {"msg": f"{len(camadas)} camadas recebidas e salvas com sucesso"}

@app.get("/camadas", response_model=List[Camada])
async def listar_camadas():
    camadas = carregar_camadas()
    return camadas
