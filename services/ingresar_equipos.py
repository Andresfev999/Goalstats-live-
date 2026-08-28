from flask import Blueprint, Flask, request, redirect, url_for, render_template, jsonify
from conf import db

ingresar_equipos_blueprint = Blueprint('ingresar_equipos', __name__)

@ingresar_equipos_blueprint.route('/principal')
def principal():
    try:
        equipos = db.equipo.find_many()
    except Exception as e:
        print(f"Error al cargar equipos: {e}")
        equipos = []
    return render_template('principal.html', equipos={'equipos': equipos})

@ingresar_equipos_blueprint.route('/ingresar_equipos', methods=['GET', 'POST'])
def ingresar_equipos():
    if request.method == 'POST':
        nombre_equipo = request.form.get('nombre_equipo')
        logo_ruta = request.form.get('logo_ruta')

        if not nombre_equipo or not logo_ruta:
            return render_template('ingresar_equipos.html', mensaje_error="Todos los campos son obligatorios")

        try:
            existente = db.equipo.find_first(where={'nombre': nombre_equipo})
            if existente:
                return render_template('ingresar_equipos.html', mensaje_error="El equipo ya está ingresado")
            
            db.equipo.create(data={
                'nombre': nombre_equipo,
                'logo': logo_ruta
            })

            return redirect(url_for('principal'))
        except Exception as e:
            return render_template('ingresar_equipos.html', mensaje_error=str(e))

    return render_template('ingresar_equipos.html')

if __name__ == '__main__':
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'una_llave_secreta_muy_segura'
    app.register_blueprint(ingresar_equipos_blueprint)
    app.run(debug=True, port=5004)
