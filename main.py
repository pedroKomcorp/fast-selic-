from fastapi import FastAPI, HTTPException
from typing import Optional
from datetime import datetime, date
from bs4 import BeautifulSoup
import requests

app = FastAPI()

class SelicScraper:
    def __init__(self):
        self.url = (
            "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/pagamentos-e-parcelamentos/taxa-de-juros-selic#Selicmensalmente"
        )
        self.selic_data = {2020: [], 2021: [], 2022: [], 2023: [], 2024: [], 2025: []}

    def fetch_data(self):
        response = requests.get(self.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        table_2020_2025 = soup.select_one('#parent-fieldname-text > table:nth-of-type(6)')
        if table_2020_2025:
            rows = table_2020_2025.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                for i, year in enumerate(range(2020, 2026), start=1):
                    if len(cells) >= i + 1:
                        month_data = cells[i].text.strip()
                        self.selic_data[year].append(month_data)

    def retorna_selic(self, ano: int, mes: int):
        try:
            mes += 1
            if mes == 13:
                mes = 1
                ano += 1
            
            # Fetch data before calculating
            self.fetch_data()

            if ano not in self.selic_data or mes < 1 or mes > 12:
                raise ValueError("Ano ou mês inválido.")

            if len(self.selic_data[ano]) < mes:
                raise ValueError("Dados insuficientes para o ano/mês especificado.")

            month_data = self.selic_data[ano][mes - 1]
            return float(month_data.replace(',', '.')) / 100
        except ValueError:
            raise HTTPException(status_code=400, detail="Não existe Selic para esta data ainda!")

scraper = SelicScraper()

def safe_float(value):
    """Converte um valor para float, retornando 0 se a conversão falhar."""
    try:
        return round(float(value.replace(',', '.')), 4)
    except (ValueError, AttributeError):
        return 0.0

@app.get("/")
def get_selic(mes_ano: Optional[str] = None):
    # If no query parameter is provided, return the full contents of selics
    if mes_ano is None:
        scraper.fetch_data()
        return {"selic_data": scraper.selic_data}
    
    # Validate the input format (mmyyyy)
    if len(mes_ano) != 6 or not mes_ano.isdigit():
        raise HTTPException(status_code=400, detail="Formato inválido. Use mmyyyy.")
    
    mes = int(mes_ano[:2])
    ano = int(mes_ano[2:])
    return {"taxa_selic": scraper.retorna_selic(ano, mes)}
