from flask import Blueprint, Flask, request, redirect, url_for, render_template, jsonify
from conf import db

registro_estadisticas_blueprint = Blueprint('registro_estadisticas', __name__)

@registro_estadisticas_blueprint.route('/registrar_datos', methods=['GET', 'POST'])
def registrar_datos():
    if request.method == 'POST':
        nombre_equipo = request.form.get('nombre_equipo')
        partidos_ganados = int(request.form.get('partidos_ganados', '0') or 0)
        partidos_empatados = int(request.form.get('partidos_empatados', '0') or 0)
        partidos_perdidos = int(request.form.get('partidos_perdidos', '0') or 0)
        puntos_totales = int(request.form.get('puntos_totales', '0') or 0)

        try:
            equipo = db.equipo.find_first(where={'nombre': nombre_equipo})
            if not equipo:
                return render_template('registrar_datos.html', mensaje_error=f"Equipo '{nombre_equipo}' no encontrado")

            stats = db.estadisticaequipo.find_first(where={'equipo_id': equipo.id})
            if stats:
                db.estadisticaequipo.update(
                    where={'id': stats.id},
                    data={
                        'partidos_ganados': partidos_ganados,
                        'partidos_empatados': partidos_empatados,
                        'partidos_perdidos': partidos_perdidos,
                        'puntos_totales': puntos_totales
                    }
                )
            else:
                db.estadisticaequipo.create(data={
                    'equipo_id': equipo.id,
                    'partidos_ganados': partidos_ganados,
                    'partidos_empatados': partidos_empatados,
                    'partidos_perdidos': partidos_perdidos,
                    'puntos_totales': puntos_totales
                })

            return redirect(url_for('principal'))
        except Exception as e:
            return render_template('registrar_datos.html', mensaje_error=str(e))

    try:
        equipos = db.equipo.find_many()
    except Exception as e:
        print(f"Error al obtener equipos: {e}")
        equipos = []

    return render_template('registrar_datos.html', equipos=equipos)

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(registro_estadisticas_blueprint)
    app.run(debug=True, port=5005)
