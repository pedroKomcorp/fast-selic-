from fastapi import FastAPI, HTTPException
from typing import Optional
from bs4 import BeautifulSoup
import requests

app = FastAPI()

class SelicScraper:
    def __init__(self):
        self.url = (
            "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/pagamentos-e-parcelamentos/taxa-de-juros-selic#Selicmensalmente"
        )
        # Initialize with years keys; the raw data will be stored as lists per year.
        self.selic_data = {2020: [], 2021: [], 2022: [], 2023: [], 2024: [], 2025: []}

    def fetch_data(self):
        response = requests.get(self.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.select_one('#parent-fieldname-text > table:nth-of-type(6)')
        if table:
            rows = table.find_all('tr')
            # For each row, loop through each year column.
            for row in rows:
                cells = row.find_all('td')
                # The table might contain duplicate data for each year so we assume the first 13 cells contain the year label + 12 months.
                for i, year in enumerate(range(2020, 2026), start=1):
                    if len(cells) >= i + 1:
                        cell_text = cells[i].text.strip()
                        self.selic_data[year].append(cell_text)

    def retorna_selic(self, ano: int, mes: int):
        try:
            # Adjust for next month if needed
            mes += 1
            if mes == 13:
                mes = 1
                ano += 1
            
            self.fetch_data()
            if ano not in self.selic_data or mes < 1 or mes > 12:
                raise ValueError("Ano ou mês inválido.")
            # Use only the first 13 items (year label + 12 months)
            data = self.selic_data[ano][:13]
            if len(data) < 13:
                raise ValueError("Dados insuficientes para o ano/mês especificado.")
            month_data = data[mes]  # mes is already adjusted (data[0] is the label)
            return month_data.replace
        except ValueError:
            raise HTTPException(status_code=400, detail="Não existe Selic para esta data ainda!")

scraper = SelicScraper()

@app.get("/")
def get_selic(mes_ano: Optional[str] = None):
    # Always update the raw data
    scraper.fetch_data()
    
    # If no query parameter is provided, return the full, formatted data.
    if mes_ano is None:
        formatted_data = {}
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        for year, values in scraper.selic_data.items():
            # Assume the first 13 elements are valid: first is a label and next 12 are monthly values.
            if len(values) >= 13:
                # Use only one copy if data is duplicated.
                data = values[:13]
                try:
                    year_label = int(data[0])
                except ValueError:
                    year_label = year
                monthly_rates = {}
                for i, rate in enumerate(data[1:]):
                    # Clean up value; if value is not available (e.g., "---" or empty), return None.
                    try:
                        monthly_rates[months[i]] = round(float(rate.replace(',', '.')), 4) if rate not in ("---", "") else None
                    except ValueError:
                        monthly_rates[months[i]] = None
                formatted_data[str(year)] = {
                    "monthly_rates": monthly_rates
                }
        return {"selic_data": formatted_data}
    
    # When the query parameter is provided, validate format (mmyyyy)
    if len(mes_ano) != 6 or not mes_ano.isdigit():
        raise HTTPException(status_code=400, detail="Formato inválido. Use mmyyyy.")
    
    mes = int(mes_ano[:2])
    ano = int(mes_ano[2:])
    return {"taxa_selic": scraper.retorna_selic(ano, mes)}
