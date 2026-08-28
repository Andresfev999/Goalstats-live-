import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from flask import Flask, redirect, url_for, Response
from services.ingresar_equipos import ingresar_equipos_blueprint
from services.registro_estadisticas import registro_estadisticas_blueprint
from services.getStats import getStats_blueprint
from services.stats_players import stats_players_blueprint
from services.stats_service import stats_service_blueprint
from services.api_football import api_football_blueprint
from services.scraper_rojadirecta import scraper_bp

app = Flask(__name__, static_folder='static')
app.secret_key = 'super_secret_key'

# Registrar Blueprints
app.register_blueprint(ingresar_equipos_blueprint)
app.register_blueprint(registro_estadisticas_blueprint)
app.register_blueprint(getStats_blueprint)
app.register_blueprint(stats_players_blueprint)
app.register_blueprint(stats_service_blueprint)
app.register_blueprint(api_football_blueprint)
app.register_blueprint(scraper_bp)

# Favicon handler
@app.route('/favicon.ico')
def favicon():
    svg_icon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#3b82f6"/><path d="M50 10 L70 30 L60 60 L40 60 L30 30 Z" fill="#ffffff"/></svg>'''
    return Response(svg_icon, mimetype='image/svg+xml')

# Redirección Directa a la vista principal sin Login
@app.route('/')
def index():
    return redirect('/principal')

@app.route('/login')
def login():
    return redirect('/principal')

@app.route('/register')
def register():
    return redirect('/principal')

@app.route('/principal')
def principal():
    return getStats_blueprint.send_static_file('../templates/principal.html')

@app.route('/estadisticas_equipos')
def estadisticas_equipos_alias():
    return redirect(url_for('getStats.estadisticas_equipos'))

@app.route('/cerrar_sesion')
def cerrar_sesion_alias():
    return redirect('/principal')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
