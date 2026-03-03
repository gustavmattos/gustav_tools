import os
import requests
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def send_teams_test_message():
    """
    Envia uma mensagem de teste para o Webhook do Microsoft Teams.
    """
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    
    print(f"Tentando enviar mensagem para: {webhook_url[:30]}...")
    
    if not webhook_url or "your_teams_webhook_url" in webhook_url:
        print("Erro: TEAMS_WEBHOOK_URL não configurado corretamente no arquivo .env")
        return False

    payload = {
        "text": "🚀 **Teste de Conexão: Automação Salesforce**\n\nEsta é uma mensagem de teste enviada manualmente para validar a conexão com o Teams."
    }

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("Sucesso! Mensagem enviada com sucesso para o Teams.")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP ao enviar mensagem: {e.response.status_code} - {e.response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ao enviar mensagem: {e}")
        return False

if __name__ == "__main__":
    send_teams_test_message()
