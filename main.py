from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
ACE_URL = "https://www.aena.es/es/infovuelos.html?airportCode=ACE&flightType=arrival"

def scrap_ace_arrivals():
    """Devuelve una lista de dicts con TODAS las llegadas a ACE que Aena publica."""
    resp = requests.get(ACE_URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tabla = soup.find("table", class_="tblFlightResults")
    if not tabla:
        return []
    vuelos = []
    for fila in tabla.find("tbody").find_all("tr"):
        cols = fila.find_all("td")
        vuelos.append({
            "vuelo"          : cols[0].get_text(strip=True),
            "origen"         : cols[1].get_text(strip=True),
            "hora_llegada"   : cols[2].get_text(strip=True),
            "estado"         : cols[3].get_text(strip=True),
            "puerta"         : cols[4].get_text(strip=True),
            "cinta"          : cols[5].get_text(strip=True),
            "parking"        : cols[6].get_text(strip=True) if len(cols) > 6 else "-",
        })
    return vuelos

@app.route("/api/buscar")
def buscar_por_origen():
    origen = request.args.get("origen", "").strip()
    if not origen:
        return jsonify({"error": "Parámetro 'origen' requerido"}), 400
    lista = scrap_ace_arrivals()
    filtrados = [v for v in lista if origen.lower() in v["origen"].lower()]
    if not filtrados:
        return jsonify({"error": "No se encontraron vuelos con ese origen"}), 404
    return jsonify(filtrados)

# Ruta antigua opcional (sigue funcionando si la necesitas)
@app.route("/api/vuelo")
def vuelo_info():
    vuelo = request.args.get("vuelo")
    destino = request.args.get("destino", "ACE")
    if not vuelo:
        return jsonify({"error": "Parámetro 'vuelo' requerido"}), 400
    url = f"{ACE_URL}&flightNumber={vuelo}"
    resp = requests.get(url, timeout=15)
    if resp.status_code != 200:
        return jsonify({"error": "No se pudo obtener datos de Aena"}), 500
    soup = BeautifulSoup(resp.text, "html.parser")
    fila = soup.find("table", class_="tblFlightResults")
    if not fila:
        return jsonify({"error": "Vuelo no encontrado"}), 404
    cols = fila.find("tbody").find("tr").find_all("td")
    data = {
        "vuelo"        : cols[0].get_text(strip=True),
        "origen"       : cols[1].get_text(strip=True),
        "hora_llegada" : cols[2].get_text(strip=True),
        "estado"       : cols[3].get_text(strip=True),
        "puerta"       : cols[4].get_text(strip=True),
        "cinta"        : cols[5].get_text(strip=True),
        "parking"      : cols[6].get_text(strip=True) if len(cols) > 6 else "-"
    }
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
