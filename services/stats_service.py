from flask import Blueprint, Flask, request, jsonify
import numpy as np
from conf import db

stats_service_blueprint = Blueprint('stats_service', __name__)

@stats_service_blueprint.route('/estadisticas/equipo', methods=['GET'])
def estadisticas_equipo():
    nombre_equipo = request.args.get('nombre')
    if not nombre_equipo:
        return jsonify({'error': 'Falta el nombre del equipo'}), 400

    try:
        equipo = db.equipo.find_first(where={'nombre': nombre_equipo}, include={'stats': True})

        if not equipo or not equipo.stats:
            return jsonify({'error': 'Equipo o estadísticas no encontradas'}), 404

        st = equipo.stats[0]

        matriz_resultados = np.array([st.partidos_ganados, st.partidos_empatados, st.partidos_perdidos], dtype=float)
        total_partidos = float(np.sum(matriz_resultados))

        if total_partidos == 0:
            estadisticas = {
                "porcentaje_partidos_ganados": 0.0,
                "porcentaje_partidos_empatados": 0.0,
                "porcentaje_partidos_perdidos": 0.0,
                "puntos_totales": st.puntos_totales,
                "promedio_puntos_partido": 0.0
            }
        else:
            porcentajes = (matriz_resultados / total_partidos) * 100.0
            promedio_puntos = float(st.puntos_totales) / total_partidos
            estadisticas = {
                "porcentaje_partidos_ganados": round(float(porcentajes[0]), 2),
                "porcentaje_partidos_empatados": round(float(porcentajes[1]), 2),
                "porcentaje_partidos_perdidos": round(float(porcentajes[2]), 2),
                "puntos_totales": st.puntos_totales,
                "promedio_puntos_partido": round(promedio_puntos, 2)
            }

        return jsonify(estadisticas)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stats_service_blueprint.route('/estadisticas/tabla_posiciones', methods=['GET'])
def tabla_posiciones():
    league_id = request.args.get('league_id', type=int) or 140
    try:
        # Filtrar ESTRICTAMENTE solo por la liga seleccionada
        equipos = db.equipo.find_many(where={'league_id': league_id}, include={'stats': True})

        if not equipos:
            return jsonify([])

        datos_equipos = []
        for eq in equipos:
            st = eq.stats[0] if eq.stats else None
            pg = st.partidos_ganados if st else 0
            pe = st.partidos_empatados if st else 0
            pp = st.partidos_perdidos if st else 0
            pts = st.puntos_totales if st else 0
            pj = pg + pe + pp
            datos_equipos.append([pts, pj, pg, pe, pp])

        matriz_global = np.array(datos_equipos)
        indices_ordenados = np.argsort(-matriz_global[:, 0])

        tabla = []
        for rank, idx in enumerate(indices_ordenados, start=1):
            eq = equipos[idx]
            row = matriz_global[idx]
            tabla.append({
                'posicion': rank,
                'nombre': eq.nombre,
                'logo': eq.logo,
                'puntos': int(row[0]),
                'pj': int(row[1]),
                'pg': int(row[2]),
                'pe': int(row[3]),
                'pp': int(row[4])
            })

        return jsonify(tabla)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(stats_service_blueprint)
    app.run(debug=True, port=5001)
