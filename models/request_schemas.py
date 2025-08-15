#backend/models/request_schemas.py
from pydantic import BaseModel
from typing import List, Optional, Dict

class Filter(BaseModel):
    table: str
    column: str
    operator: str  # Ex: '=', 'LIKE', '>', etc.
    value: str

class BuildTableRequest(BaseModel):
    selected_columns: List[str]  # formato: ["tabela.coluna"]
    filters: Optional[List[Filter]] = []