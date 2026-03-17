import sys
import os

# Adiciona o caminho para que o Python encontre a pasta backend_api
sys.path.append(os.path.join(os.getcwd(), "backend_api"))

try:
    from db import engine, Base
    import models  # Importa os modelos para o SQLAlchemy mapear as tabelas
    
    print(" Conectando ao banco de dados do Render...")
    print(" Criando tabelas do JURISDAY...")
    
    # Comando que efetivamente cria as tabelas no PostgreSQL do Render
    Base.metadata.create_all(bind=engine)
    
    print(" Sucesso! Tabelas criadas. O Erro 500 deve sumir agora.")
    
except Exception as e:
    print(f" Erro ao inicializar banco: {e}")