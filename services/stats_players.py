from flask import Blueprint, Flask, request, jsonify
import numpy as np
from conf import db

stats_players_blueprint = Blueprint('stats_players', __name__)

@stats_players_blueprint.route('/estadisticas/jugadores', methods=['GET'])
def estadisticas_jugadores():
    nombre_equipo = request.args.get('nombre_equipo')
    if not nombre_equipo:
        return jsonify({'error': 'Falta el nombre del equipo'}), 400

    try:
        jugadores = db.jugador.find_many(where={'nombre_equipo': nombre_equipo})
        if not jugadores:
            return jsonify({
                "goles_por_remate": 0,
                "tarjetas_amarillas_por_rojas": 0,
                "mejor_goleador": None,
                "jugador_mayor_riesgo": None,
            })

        datos = np.array([[j.goles, j.remates_al_arco, j.tarjetas_amarillas, j.tarjetas_rojas] for j in jugadores])

        sumas_totales = datos.sum(axis=0)

        goles_por_remate = sumas_totales[0] / sumas_totales[1] if sumas_totales[1] > 0 else 0
        tarjetas_amarillas_por_rojas = sumas_totales[2] / sumas_totales[3] if sumas_totales[3] > 0 else 0

        mejor_goleador_index = np.argmax(datos[:, 0])
        mejor_goleador = jugadores[mejor_goleador_index].nombre

        jugador_mayor_riesgo_index = np.argmax(datos[:, 3])
        jugador_mayor_riesgo = jugadores[jugador_mayor_riesgo_index].nombre

        return jsonify({
            "goles_por_remate": round(float(goles_por_remate), 2),
            "tarjetas_amarillas_por_rojas": round(float(tarjetas_amarillas_por_rojas), 2),
            "mejor_goleador": mejor_goleador,
            "jugador_mayor_riesgo": jugador_mayor_riesgo,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(stats_players_blueprint)
    app.run(debug=True, port=5002)
