import os
import time
import requests
from dotenv import load_dotenv
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# URLs de exemplo/configuração
SF_INSTANCE_URL = "https://dynamoxbr.lightning.force.com" # Apenas para referência visual

def connect_to_salesforce():
    """
    Conecta ao Salesforce usando Username, Password e Security Token.
    Não requer Client ID/Secret.
    """
    username = os.getenv("SF_USERNAME")
    password = os.getenv("SF_PASSWORD")
    token = os.getenv("SF_TOKEN")

    try:
        sf = Salesforce(username=username, password=password, security_token=token)
        print("Conectado ao Salesforce com sucesso!")
        return sf
    except SalesforceAuthenticationFailed as e:
        print(f"Erro de autenticação no Salesforce: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao conectar ao Salesforce: {e}")
        return None

def send_teams_notification(message):
    """
    Envia uma mensagem para o Webhook do Microsoft Teams.
    """
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    
    if not webhook_url or "your_teams_webhook_url" in webhook_url:
        print("Erro: TEAMS_WEBHOOK_URL não configurado corretamente no arquivo .env")
        return False

    payload = {
        "text": message
    }

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem para o Teams: {e}")
        return False

def get_new_cases(sf, last_check_time):
    """
    Busca casos novos ('Casos em Aberto GERAL') baseados na data de criação.
    """
    # Consulta SOQL para buscar casos abertos criados após o último check
    # Ajuste o filtro conforme o critério 'Casos em Aberto GERAL'
    query = (
        "SELECT Id, CaseNumber, Subject, Description, CreatedDate "
        "FROM Case "
        f"WHERE IsClosed = false AND CreatedDate > {last_check_time} "
        "ORDER BY CreatedDate DESC"
    )
    
    try:
        results = sf.query(query)
        return results.get('records', [])
    except Exception as e:
        print(f"Erro ao buscar casos: {e}")
        return []

def main():
    print("--- Monitoramento Salesforce Iniciado ---")
    
    sf = connect_to_salesforce()
    if not sf:
        return

    # Envia mensagem inicial
    send_teams_notification("🤖 Script de Monitoramento de Casos Iniciado.")

    # ISO 8601 format for Salesforce SOQL
    # Começamos verificando casos criados nos últimos 5 minutos
    last_check_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 300))

    while True:
        print(f"[{time.strftime('%H:%M:%S')}] Verificando novos casos...")
        
        new_cases = get_new_cases(sf, last_check_time)
        
        if new_cases:
            print(f"Encontrados {len(new_cases)} novos casos!")
            for case in new_cases:
                case_id = case['Id']
                case_num = case['CaseNumber']
                subject = case.get('Subject', 'Sem Assunto')
                
                # Link para o caso no Lightning
                link = f"{SF_INSTANCE_URL}/lightning/r/Case/{case_id}/view"
                
                msg = f"🔔 **Novo Caso Recebido!**\n\n**Número:** {case_num}\n**Assunto:** {subject}\n[Visualizar no Salesforce]({link})"
                
                if send_teams_notification(msg):
                    print(f"Notificação enviada para o caso {case_num}")
            
            # Atualiza o tempo para a próxima checagem para o tempo do caso mais novo
            # ou simplesmente para o tempo atual
            last_check_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        else:
            print("Nenhum novo caso encontrado.")

        # Aguarda 5 minutos para a próxima verificação (300 segundos)
        time.sleep(300)

if __name__ == "__main__":
    main()
