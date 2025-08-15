#app.py
import streamlit as st
import requests
import pandas as pd
from io import BytesIO

# Configuração inicial
st.set_page_config(
    page_title="DataExplorer Pro",
    page_icon="🔍",
    layout="wide"
)

# Inicialização do session_state
if 'selected_columns' not in st.session_state:
    st.session_state.selected_columns = []
if 'filters' not in st.session_state:
    st.session_state.filters = {}
if 'like_filters' not in st.session_state:
    st.session_state.like_filters = {}

# Título
st.title("🔍 DataExplorer Pro")
st.markdown("Explore seus dados com filtros avançados")

# Funções auxiliares
@st.cache_data(ttl=300)
def get_schema():
    try:
        response = requests.get("http://localhost:8000/schema")
        return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar schema: {str(e)}")
        return {}

@st.cache_data(ttl=300)
def get_distinct_values(table, column, search=None):
    try:
        params = {"search": search} if search else {}
        response = requests.get(f"http://localhost:8000/distinct/{table}/{column}", params=params)
        return response.json()
    except Exception as e:
        st.error(f"Erro ao buscar valores distintos: {str(e)}")
        return []

def download_data():
    try:
        data = {
            "selected_columns": st.session_state.selected_columns,
            "filters": {k: v for k, v in st.session_state.filters.items() if v},
            "like_filters": {k: v for k, v in st.session_state.like_filters.items() if v}
        }
        
        response = requests.post(
            "http://localhost:8000/query",
            json=data,
            stream=True
        )
        
        if response.status_code == 200:
            return pd.read_excel(BytesIO(response.content))
        else:
            st.error(f"Erro ao gerar tabela: {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro ao baixar dados: {str(e)}")
        return None

# Layout principal
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Seleção de Colunas")
    schema = get_schema()
    
    for table, columns in schema.items():
        with st.expander(f"📊 {table}"):
            # Selecionar todas as colunas
            all_key = f"all_{table}"
            if st.checkbox("Selecionar todas", key=all_key):
                for col in columns:
                    full_col = f"{table}.{col}"
                    if full_col not in st.session_state.selected_columns:
                        st.session_state.selected_columns.append(full_col)
            else:
                st.session_state.selected_columns = [
                    col for col in st.session_state.selected_columns 
                    if not col.startswith(f"{table}.")
                ]
            
            # Seleção individual
            for col in columns:
                full_col = f"{table}.{col}"
                if st.checkbox(
                    col,
                    value=full_col in st.session_state.selected_columns,
                    key=f"col_{table}_{col}"
                ):
                    if full_col not in st.session_state.selected_columns:
                        st.session_state.selected_columns.append(full_col)
                else:
                    if full_col in st.session_state.selected_columns:
                        st.session_state.selected_columns.remove(full_col)

    # Seção de Filtros
    if st.session_state.selected_columns:
        st.header("Filtros Avançados")
        
        if st.button("🔄 Limpar todos os filtros"):
            st.session_state.filters = {}
            st.session_state.like_filters = {}
            st.experimental_rerun()
        
        for full_col in st.session_state.selected_columns:
            table, col = full_col.split(".")
            st.subheader(f"{table}.{col}")
            
            # Filtro LIKE
            like_key = f"like_{table}_{col}"
            like_value = st.text_input(
                "Filtro com padrão (ex: J%, %ana%)",
                key=like_key,
                help="Use % como curinga. Ex: J% para valores que começam com J"
            )
            
            if like_value:
                st.session_state.like_filters[full_col] = like_value
                # Remove filtros exatos se estiver usando LIKE
                if full_col in st.session_state.filters:
                    del st.session_state.filters[full_col]
            elif full_col in st.session_state.like_filters:
                del st.session_state.like_filters[full_col]
            
            # Filtro de valores exatos (só aparece se não estiver usando LIKE)
            if not like_value:
                search_key = f"search_{table}_{col}"
                search_term = st.text_input(
                    "Pesquisar valores exatos",
                    key=search_key
                )
                
                values = get_distinct_values(table, col, search_term if search_term else None)
                
                if values:
                    selected = st.multiselect(
                        "Selecionar valores",
                        values,
                        default=st.session_state.filters.get(full_col, []),
                        key=f"select_{table}_{col}"
                    )
                    
                    if selected:
                        st.session_state.filters[full_col] = selected
                    elif full_col in st.session_state.filters:
                        del st.session_state.filters[full_col]

with col2:
    st.header("Resumo da Consulta")
    
    # Colunas selecionadas
    st.subheader("📋 Colunas Selecionadas")
    if st.session_state.selected_columns:
        for col in st.session_state.selected_columns:
            table, column = col.split(".")
            st.markdown(f"- **{column}** (*{table}*)")
    else:
        st.info("Nenhuma coluna selecionada")
    
    # Filtros aplicados
    st.subheader("⚙️ Filtros Aplicados")
    if st.session_state.filters or st.session_state.like_filters:
        for col, values in st.session_state.filters.items():
            if values:
                table, column = col.split(".")
                st.markdown(f"**{column}** (*{table}*) - Valores exatos")
                for val in values:
                    st.markdown(f"  - {val}")
        
        for col, pattern in st.session_state.like_filters.items():
            if pattern:
                table, column = col.split(".")
                st.markdown(f"**{column}** (*{table}*) - Padrão LIKE")
                st.markdown(f"  - `{pattern}`")
    else:
        st.info("Nenhum filtro aplicado")
    
    # Botão de execução
    if st.button(
        "▶️ Executar Consulta",
        disabled=not st.session_state.selected_columns,
        type="primary",
        use_container_width=True
    ):
        with st.spinner("Processando..."):
            df = download_data()
            if df is not None:
                st.success("Consulta realizada com sucesso!")
                st.dataframe(df)
                
                # Opção para download
                # Substituir o botão CSV por:
                excel = BytesIO()
                df.to_excel(excel, index=False)
                st.download_button(
                    "💾 Baixar como Excel",
                    excel.getvalue(),
                    "resultado.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

# Rodapé
st.divider()
st.caption("DataExplorer Pro v1.0 | © 2023")