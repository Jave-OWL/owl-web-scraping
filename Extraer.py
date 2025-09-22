import pandas as pd

class LinkExtractor:
    def __init__(self, file_path):
        self.file_path = file_path

    def extract_links(self):
        df = pd.read_excel(self.file_path, sheet_name="Hoja1", header=None)
        df.fillna("", inplace=True)

        administradora_actual = ""
        data = []

        for _, row in df.iterrows():
            admin = str(row.iloc[0]).strip()   # Columna A
            link = str(row.iloc[1]).strip()    # Columna B

            if admin and not link:
                # Si hay texto en col A pero col B está vacía -> es un administrador
                administradora_actual = admin

            elif admin and link:
                # Si hay texto en col A y link en col B -> es un fondo
                data.append((administradora_actual, admin, link))

        return data

    def extract_month_year(self):
        df = pd.read_excel(self.file_path, header=None, sheet_name="Hoja1")
        df.fillna("", inplace=True)

        mes = str(df.iloc[1, 8]).strip()   # Celda I3 -> fila 2, columna 8
        año = str(df.iloc[1, 9]).strip()   # Celda J3 -> fila 2, columna 9

        return mes, año
