import json

class LinkExtractor:
    def __init__(self, file_path):
        self.file_path = file_path

    def extract_links(self):
        # Leer el archivo JSON
        with open(self.file_path, "r", encoding="utf-8") as f:
            data_json = json.load(f)

        data = []
        # Recorrer cada administradora (clave principal)
        for administradora, fondos in data_json.items():
            # fondos es un diccionario {fondo: link}
            for fondo, link in fondos.items():
                # Agregamos una tupla (administradora, fondo, link)
                data.append((administradora, fondo, link))

        return data