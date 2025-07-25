from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, os, re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)                        # permite CORS

ACE_URL = "https://www.aena.es/es/infovuelos.html?airportCode=ACE&flightType=arrival"

def scrap_ace_arrivals():
    r = requests.get(ACE_URL, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
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

def coincide(celda: str, q: str) -> bool:
    q = q.upper()
    if len(q) == 3:                             # IATA
        return celda.startswith(q) or q in celda
    return re.sub(r"\s+","",q) in re.sub(r"\s+","",celda)

@app.route("/api/buscar")
def buscar():
    q = request.args.get("origen","").strip()
    if not q:
        return jsonify({"error":"Parámetro 'origen' requerido"}), 400
    try:
        vuelos = scrap_ace_arrivals()
    except Exception as e:
        return jsonify({"error":"Aena no responde","detalle":str(e)}), 502
    filtrados = [v for v in vuelos if coincide(v["origen"], q)]
    if not filtrados:
        return jsonify({"error":"No se encontraron vuelos con ese origen"}), 404
    return jsonify(filtrados)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))   # Render envía PORT
    app.run(host="0.0.0.0", port=port)
