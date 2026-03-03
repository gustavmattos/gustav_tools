import os
from dotenv import load_dotenv
from simple_salesforce import Salesforce

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def test_salesforce_query():
    username = os.getenv("SF_USERNAME")
    password = os.getenv("SF_PASSWORD")
    token = os.getenv("SF_TOKEN")

    print(f"Conectando ao Salesforce como: {username}...")
    try:
        sf = Salesforce(username=username, password=password, security_token=token)
        print("Conexão estabelecida!")
        
        # Testar a query exata usada no main.py
        # Vamos usar um lookback de 24 horas para garantir que pegamos algo recente
        import time
        last_check_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - (24 * 60 * 60)))
        
        query = (
            "SELECT Id, CaseNumber, Subject, Status, IsClosed, CreatedDate "
            "FROM Case "
            f"WHERE IsClosed = false AND CreatedDate > {last_check_time} "
            "ORDER BY CreatedDate DESC"
        )
        
        print(f"Executando query: {query}")
        results = sf.query(query)
        records = results.get('records', [])
        
        print(f"Número de casos encontrados (últimas 24h): {len(records)}")
        for rec in records[:5]: # Mostrar apenas os 5 primeiros
            print(f"- Caso: {rec['CaseNumber']} | Status: {rec['Status']} | Assunto: {rec['Subject']} | Criado: {rec['CreatedDate']}")
            
        return True
    except Exception as e:
        print(f"Erro ao testar Salesforce: {e}")
        return False

if __name__ == "__main__":
    test_salesforce_query()
