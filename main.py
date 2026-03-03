import os
import time
import sys
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
    # Consulta SOQL para buscar casos abertos:
    # 1. Criados após o último check (Novos Casos)
    # 2. Com Status Marco = 'Alerta'
    query = (
        "SELECT Id, CaseNumber, Subject, Description, CreatedDate, Status_Marco__c "
        "FROM Case "
        f"WHERE IsClosed = false AND (CreatedDate > {last_check_time} OR Status_Marco__c = 'Alerta') "
        "ORDER BY CreatedDate DESC"
    )
    
    try:
        results = sf.query(query)
        return results.get('records', [])
    except Exception as e:
        print(f"Erro ao buscar casos: {e}")
        return []

def main():
    # Verifica se deve rodar apenas uma vez (para GitHub Actions)
    run_once = "--once" in sys.argv
    
    if not run_once:
        print("--- Monitoramento Salesforce Iniciado (Modo Loop) ---")
    else:
        print("--- Monitoramento Salesforce Iniciado (Modo Execução Única) ---")
    
    sf = connect_to_salesforce()
    if not sf:
        return

    # No modo loop envia mensagem inicial. No GitHub Actions não precisa.
    if not run_once:
        send_teams_notification("🤖 Script de Monitoramento de Casos Iniciado.")

    # ISO 8601 format for Salesforce SOQL
    # Modo Local: olhamos os últimos 60 minutos na partida para não perder nada
    # Modo GitHub: 120 minutos (margem de segurança)
    lookback_minutes = 120 if run_once else 60
    last_check_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - (lookback_minutes * 60)))
    
    print(f"Buscando casos criados desde: {last_check_time} (UTC)")

    # Conjunto para evitar duplicidade de alertas de Marco (apenas no modo loop)
    notified_milestones = set()

    while True:
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Verificando novos casos e alertas...")
            
            new_records = get_new_cases(sf, last_check_time)
            
            if new_records:
                current_time_utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                
                for case in new_records:
                    case_id = case['Id']
                    case_num = case['CaseNumber']
                    subject = case.get('Subject', 'Sem Assunto')
                    status_marco = case.get('Status_Marco__c')
                    created_date = case['CreatedDate']
                    
                    link = f"{SF_INSTANCE_URL}/lightning/r/Case/{case_id}/view"
                    
                    # Lógica 1: Caso Realmente Novo (Criado após o last_check_time)
                    if created_date > last_check_time:
                        msg = f"🔔 **Novo Caso Recebido!**\n\n**Número:** {case_num}\n**Assunto:** {subject}\n[Visualizar no Salesforce]({link})"
                        if send_teams_notification(msg):
                            print(f"Notificação de novo caso enviada: {case_num}")

                    # Lógica 2: Alerta de Marco
                    if status_marco == 'Alerta':
                        if case_id not in notified_milestones:
                            msg = f"⚠️ **ALERTA DE MARCO!**\n\n**Caso:** {case_num}\n**Assunto:** {subject}\n**Status:** Em Alerta\n[Visualizar no Salesforce]({link})"
                            if send_teams_notification(msg):
                                print(f"Notificação de ALERTA enviada: {case_num}")
                                notified_milestones.add(case_id)
                    elif case_id in notified_milestones:
                        # Se saiu do status alerta, removemos do conjunto para permitir novo alerta no futuro
                        notified_milestones.remove(case_id)
                
                # Para novos casos, atualizamos o cursor de tempo
                # Usamos o tempo da execução para evitar repetições na próxima query
                last_check_time = current_time_utc
            else:
                print("Nada de novo encontrado.")

        except Exception as e:
            print(f"Erro detectado no loop: {e}. Tentando reconectar...")
            time.sleep(10)
            sf = connect_to_salesforce()
            continue

        # Se for modo execução única, encerra aqui
        if run_once:
            print("Execução única finalizada.")
            break

        # Aguarda 5 minutos para a próxima verificação
        time.sleep(300)

if __name__ == "__main__":
    main()
