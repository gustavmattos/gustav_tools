import os
from dotenv import load_dotenv
from simple_salesforce import Salesforce

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def list_case_fields():
    username = os.getenv("SF_USERNAME")
    password = os.getenv("SF_PASSWORD")
    token = os.getenv("SF_TOKEN")

    try:
        sf = Salesforce(username=username, password=password, security_token=token)
        desc = sf.Case.describe()
        
        print("Buscando campos que possam ser 'Status Marco'...")
        for field in desc['fields']:
            label = field['label']
            name = field['name']
            if 'Marco' in label or 'Status' in label or 'Milestone' in name or 'Status' in name:
                print(f"Label: {label} | API Name: {name}")
                
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

if __name__ == "__main__":
    list_case_fields()
