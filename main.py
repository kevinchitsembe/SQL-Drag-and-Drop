# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
import uuid
import os

from db import get_oracle_engine
from utils.query_builder import build_query
from crud.metadata import get_tables, get_columns, get_distinct_values

app = FastAPI()

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, limitar para o domínio específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 Estrutura de entrada
class QueryRequest(BaseModel):
    selected_columns: List[str]
    filters: Dict[str, List[str]] = {}
    like_filters: Dict[str, str] = {}  # Novo campo para filtros LIKE

# 📌 Endpoint principal: constrói e executa a query
@app.post("/query")
def run_query(request: QueryRequest):
    try:
        # Modificamos a build_query para aceitar um novo parâmetro
        query = build_query(
            request.selected_columns, 
            request.filters,
            request.like_filters  # Novo parâmetro
        )
        engine = get_oracle_engine()
        df = pd.read_sql_query(query, engine)

        filename = f"resultado_{uuid.uuid4().hex}.xlsx"
        filepath = os.path.join("downloads", filename)
        os.makedirs("downloads", exist_ok=True)
        df.to_excel(filepath, index=False)

        return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=filename)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Endpoint: listar tabelas e colunas disponíveis
@app.get("/schema")
def get_schema():
    try:
        schema = {}
        tables = get_tables()
        
        for table in tables:
            schema[table] = get_columns(table)
            
        return schema

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/distinct/{table}/{column}")
def get_distinct_column_values(table: str, column: str, search: str = None, limit: int = 10):
    try:
        values = get_distinct_values(table, column, search)
        return values
    except Exception as e:
        print(f"Erro no endpoint /distinct/{table}/{column}: {str(e)}")
        # Retornar uma lista vazia em vez de um erro HTTP
        # Isso evitará o erro 500 e o frontend pode lidar com uma lista vazia
        return []