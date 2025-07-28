from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI()
ARQUIVO_DB = "camadas_db.json"

class Camada(BaseModel):
    Espessura: float
    Peso: float
    NSPT: int
    Descrição: str

class PerfilSondagem(BaseModel):
    camadas: List[Camada]
    nivel_agua: Optional[float] = None

def salvar_perfil(perfil: PerfilSondagem):
    with open(ARQUIVO_DB, "w", encoding="utf-8") as f:
        json.dump(perfil.dict(), f, ensure_ascii=False, indent=2)

def carregar_perfil() -> PerfilSondagem:
    if not os.path.exists(ARQUIVO_DB):
        return PerfilSondagem(camadas=[])
    with open(ARQUIVO_DB, "r", encoding="utf-8") as f:
        dados = json.load(f)
        return PerfilSondagem(**dados)

@app.post("/camadas")
async def receber_camadas(perfil: PerfilSondagem):
    salvar_perfil(perfil)
    return {
        "msg": f"{len(perfil.camadas)} camadas recebidas e salvas com sucesso",
        "nivel_agua": perfil.nivel_agua
    }

@app.get("/camadas", response_model=PerfilSondagem)
async def listar_camadas():
    return carregar_perfil()
