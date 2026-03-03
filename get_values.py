import os
from dotenv import load_dotenv
from simple_salesforce import Salesforce

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def get_picklist_values():
    username = os.getenv("SF_USERNAME")
    password = os.getenv("SF_PASSWORD")
    token = os.getenv("SF_TOKEN")

    try:
        sf = Salesforce(username=username, password=password, security_token=token)
        desc = sf.Case.describe()
        
        for field in desc['fields']:
            if field['name'] == 'Status_Marco__c':
                print(f"Valores para {field['label']} ({field['name']}):")
                for val in field['picklistValues']:
                    print(f"- {val['label']} (Valor: {val['value']})")
                
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

if __name__ == "__main__":
    get_picklist_values()
