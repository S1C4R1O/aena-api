from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/api/vuelo")
def vuelo_info():
    vuelo = request.args.get("vuelo")
    destino = request.args.get("destino")
    if not vuelo or not destino:
        return jsonify({"error":"Parámetros 'vuelo' y 'destino' obligatorios"}), 400

    # URL de Aena Infovuelos para llegadas
    url = f"https://www.aena.es/es/infovuelos.html?airportCode={destino}&flightType=arrival&flightNumber={vuelo}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return jsonify({"error":"No se pudo obtener datos de Aena", "status": resp.status_code}), 500

    soup = BeautifulSoup(resp.text, "html.parser")
    try:
        tabla = soup.find("table", class_="tblFlightResults")
        fila = tabla.find("tbody").find("tr")
        cols = fila.find_all("td")
        data = {
            "vuelo": cols[0].get_text(strip=True),
            "origen": cols[1].get_text(strip=True),
            "llegada_hora": cols[2].get_text(strip=True),
            "estado": cols[3].get_text(strip=True),
            "puerta_embarque": cols[4].get_text(strip=True),
            "cinta_equipaje": cols[5].get_text(strip=True),
            "parking": cols[6].get_text(strip=True) if len(cols)>6 else "-"
        }
    except Exception as e:
        return jsonify({"error":"Formato inesperado de respuesta", "detalle": str(e)}), 500

    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
