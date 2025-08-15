# backend/utils/query_builder.py
from typing import List, Dict, Set

# 🔗 Mapa de relações entre tabelas (chaves estrangeiras)
JOIN_RELATIONS = {
    ("CONSULTAS", "PACIENTE"): "CONSULTAS.ID_PACIENTE = PACIENTE.ID_PACIENTE",
    ("PACIENTE", "CONSULTAS"): "PACIENTE.ID_PACIENTE = CONSULTAS.ID_PACIENTE",
    # Adicione outras relações aqui conforme for expandindo a base
}

def find_join_path(tables: Set[str]) -> List[str]:
    """
    Encontra um caminho de JOINs entre as tabelas usando um algoritmo simples.
    Retorna uma lista com as cláusulas JOIN.
    """
    if len(tables) <= 1:
        return list(tables)
    
    tables_list = list(tables)
    joins = [tables_list[0]]
    connected = {tables_list[0]}
    
    # Tenta conectar todas as tabelas
    while len(connected) < len(tables):
        found_connection = False
        
        for base in connected.copy():
            for target in tables - connected:
                # Verifica se existe uma relação direta
                if (base, target) in JOIN_RELATIONS:
                    join_condition = JOIN_RELATIONS[(base, target)]
                    joins.append(f"JOIN {target} ON {join_condition}")
                    connected.add(target)
                    found_connection = True
                    break
                elif (target, base) in JOIN_RELATIONS:
                    join_condition = JOIN_RELATIONS[(target, base)]
                    joins.append(f"JOIN {target} ON {join_condition}")
                    connected.add(target)
                    found_connection = True
                    break
            
            if found_connection:
                break
        
        if not found_connection:
            raise ValueError(f"Não foi possível encontrar um caminho de JOIN entre as tabelas: {tables}")
    
    return joins

def build_from_clause(tables: Set[str]) -> str:
    """
    Constrói o FROM com JOINs dinâmicos com base nas relações conhecidas.
    """
    if not tables:
        raise ValueError("Nenhuma tabela foi especificada.")
        
    joins = find_join_path(tables)
    return "FROM " + "\n".join(joins)

def build_query(
    selected_columns: List[str], 
    filters: Dict[str, List[str]],
    like_filters: Dict[str, str] = None
) -> str:
    """Constrói query SQL com filtros normais e LIKE"""
    if not selected_columns:
        raise ValueError("Nenhuma coluna selecionada.")

    tables = set(col.split('.')[0] for col in selected_columns)
    from_clause = build_from_clause(tables)
    select_clause = "SELECT DISTINCT " + ", ".join(selected_columns)

    where_clauses = []
    
    # Filtros normais (IN ou =)
    for full_col, values in filters.items():
        if not values:
            continue
            
        quoted_vals = ", ".join(f"'{val}'" for val in values)
        if len(values) == 1:
            where_clauses.append(f"{full_col} = {quoted_vals}")
        else:
            where_clauses.append(f"{full_col} IN ({quoted_vals})")

    # Filtros LIKE
    if like_filters:
        for full_col, like_pattern in like_filters.items():
            if like_pattern:
                # Remove % se o usuário já tiver colocado
                clean_pattern = like_pattern.replace('%', '')
                where_clauses.append(f"{full_col} LIKE '%{clean_pattern}%' ESCAPE '\\'")

    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query = f"""
    {select_clause}
    {from_clause}
    {where_clause}
    FETCH FIRST 1000 ROWS ONLY
    """
    return query.strip()