from flask import Flask, request, jsonify
import requests, re
from bs4 import BeautifulSoup

app = Flask(__name__)
ACE_URL = "https://www.aena.es/es/infovuelos.html?airportCode=ACE&flightType=arrival"

def scrap_ace_arrivals():
    resp = requests.get(ACE_URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tabla = soup.find("table", class_="tblFlightResults")
    if not tabla:
        return []
    vuelos = []
    for fila in tabla.find("tbody").find_all("tr"):
        cols = fila.find_all("td")
        origen = cols[1].get_text(strip=True).upper()
        vuelos.append({
            "vuelo"       : cols[0].get_text(strip=True),
            "origen"      : origen,
            "hora_llegada": cols[2].get_text(strip=True),
            "estado"      : cols[3].get_text(strip=True),
            "puerta"      : cols[4].get_text(strip=True),
            "cinta"       : cols[5].get_text(strip=True),
            "parking"     : cols[6].get_text(strip=True) if len(cols) > 6 else "-"
        })
    return vuelos

def coincide(origen_celda: str, consulta: str) -> bool:
    """Devuelve True si la consulta (IATA o texto) coincide con el string de origen de Aena."""
    c = consulta.upper()
    if len(c) == 3:                      # posible IATA
        return origen_celda.startswith(c) or c in origen_celda
    # texto → quitar espacios y comparar parcial
    return re.sub(r"\s+", "", c) in re.sub(r"\s+", "", origen_celda)

@app.route("/api/buscar")
def buscar_por_origen():
    q = request.args.get("origen", "").strip()
    if not q:
        return jsonify({"error": "Parámetro 'origen' requerido"}), 400
    vuelos = scrap_ace_arrivals()
    filtrados = [v for v in vuelos if coincide(v["origen"], q)]
    if not filtrados:
        return jsonify({"error": "No se encontraron vuelos con ese origen"}), 404
    return jsonify(filtrados)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
