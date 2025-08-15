# backend/crud/metadata.py
from sqlalchemy import text
from db import get_oracle_engine

engine = get_oracle_engine()

SCHEMA_OWNER = "APP_USER"  

def get_tables():
    """
    Retorna uma lista com os nomes das tabelas do schema.
    """
    query = """
    SELECT table_name 
    FROM all_tables 
    WHERE owner = :owner
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"owner": SCHEMA_OWNER})
        return [row[0] for row in result]


def get_columns(table_name: str):
    """
    Retorna os nomes das colunas de uma tabela específica.
    """
    query = """
    SELECT column_name 
    FROM all_tab_columns 
    WHERE owner = :owner 
    AND table_name = :table_name
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"owner": SCHEMA_OWNER, "table_name": table_name.upper()})
        return [row[0] for row in result]

def get_distinct_values(table_name: str, column_name: str, search_term: str = None):
    """
    Retorna os valores distintos de uma coluna específica de uma tabela.
    Melhorada para maior robustez.
    """
    try:
        # Garantir que os nomes das tabelas/colunas sejam bem formados
        table_name = table_name.strip().upper()
        column_name = column_name.strip().upper()
        
        base_query = f"""
        SELECT DISTINCT {column_name}
        FROM {SCHEMA_OWNER}.{table_name}
        WHERE {column_name} IS NOT NULL
        """
        
        # Parâmetros para a query
        params = {}
        
        # Adicionar filtro de pesquisa se fornecido
        if search_term:
            base_query += f" AND UPPER({column_name}) LIKE UPPER(:search_term)"
            params["search_term"] = f"%{search_term}%"
        
        base_query += f"""
        ORDER BY {column_name}
        FETCH FIRST 10 ROWS ONLY
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(base_query), params)
            values = [str(row[0]) if row[0] is not None else "" for row in result]
            return values
            
    except Exception as e:
        # Logar o erro para diagnóstico e retornar lista vazia
        print(f"Erro ao buscar valores distintos para {table_name}.{column_name}: {str(e)}")
        return []