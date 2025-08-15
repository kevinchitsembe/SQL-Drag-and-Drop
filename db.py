#backend/db.py
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def get_oracle_engine():
    """Estabelece uma conexão com o Oracle Database usando SQLAlchemy."""
    oracle_host = os.getenv("ORACLE_HOST")
    oracle_port = os.getenv("ORACLE_PORT")
    oracle_service_name = os.getenv("ORACLE_SERVICE_NAME")
    oracle_user = os.getenv("ORACLE_USER")
    oracle_password = os.getenv("ORACLE_PASSWORD")

    # String de conexão para SQLAlchemy
    dsn = f"oracle+cx_oracle://{oracle_user}:{oracle_password}@{oracle_host}:{oracle_port}/?service_name={oracle_service_name}"
    return create_engine(dsn, pool_size=5, max_overflow=10)