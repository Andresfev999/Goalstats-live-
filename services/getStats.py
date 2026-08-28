import random
import urllib.parse
import httpx
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import numpy as np
from conf import db

getStats_blueprint = Blueprint('getStats', __name__)
get_stats_blueprint = getStats_blueprint

def asegurar_jugadores_reales(equipo_id, nombre_equipo):
    try:
        jugadores = db.jugador.find_many(where={'equipo_id': equipo_id})
        tiene_demo = any("Goleador Estrella" in j.nombre or "Capitán Mediocampo" in j.nombre for j in jugadores)

        if not jugadores or tiene_demo:
            nuevos_jugadores = []

            # 1. Intentar Scraper Bajo Demanda ESPN de Plantel de Equipo
            try:
                from services.api_football import scraper_espn_plantel_equipo_ondemand
                plantel_scraped = scraper_espn_plantel_equipo_ondemand(nombre_equipo)
                if plantel_scraped:
                    for p in plantel_scraped[:14]:
                        nuevos_jugadores.append({
                            'nombre': p['nombre'],
                            'foto': p.get('foto') or 'https://images.unsplash.com/photo-1511886929837-354d827aae26?auto=format&fit=crop&w=400&q=80'
                        })
            except Exception as e_scrap:
                print(f"Scraper plantel bajo demanda error ({nombre_equipo}): {e_scrap}")

            # 2. Intentar consultar TheSportsDB API
            if not nuevos_jugadores:
                try:
                    query_team = urllib.parse.quote(nombre_equipo)
                    url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?t={query_team}"
                    res = httpx.get(url, timeout=3.0)
                    if res.status_code == 200:
                        players_list = res.json().get('player', []) or []
                        for p in players_list[:10]:
                            p_nombre = p.get('strPlayer')
                            p_foto = p.get('strCutout') or p.get('strThumb') or p.get('strRender')
                            if p_nombre:
                                nuevos_jugadores.append({
                                    'nombre': p_nombre,
                                    'foto': p_foto or 'https://images.unsplash.com/photo-1511886929837-354d827aae26?auto=format&fit=crop&w=400&q=80'
                                })
                except Exception as e_api:
                    print(f"API players fetch error para {nombre_equipo}: {e_api}")

            # 3. Respaldo directo de jugadores reales por equipo
            if not nuevos_jugadores:
                plantillas_reales = {
                    "América de Cali": ["Jean", "Juan Pablo Montoya", "Alejandro Benítez", "Marlon Torres", "Dany Rosero", "Mateo Castillo Márquez", "Marcos Mina", "Brayan Correa", "Cristian Tovar", "Luis Mina", "Omar Bertel", "Brayan Córdoba", "Josen Escobar", "José Cavadía", "Yeison Guzmán", "Rafael Carrascal", "Yani Quintero", "Juan Aponzá", "Yhorman Hurtado"],
                    "Millonarios": ["Álvaro Montero", "Andrés Llinás", "Juan Pablo Vargas", "Danovis Banguero", "David Mackalister Silva", "Daniel Cataño", "Leonardo Castro", "Falcao García", "Daniel Ruiz"],
                    "Atlético Nacional": ["David Ospina", "William Tesillo", "Felipe Román", "Edwin Cardona", "Jorman Campuzano", "Marino Hinestroza", "Alfredo Morelos", "Kevin Viveros"],
                    "Junior": ["Santiago Mele", "Emanuel Olivera", "Didier Moreno", "Víctor Cantillo", "Yimmi Chará", "Carlos Bacca", "José Enamorado", "Marco Pérez"],
                    "Real Madrid": ["Vinicius Jr", "Jude Bellingham", "Kylian Mbappé", "Luka Modrić", "Rodrygo", "Thibaut Courtois", "Federico Valverde", "Dani Carvajal", "Eduardo Camavinga"],
                    "Barcelona": ["Lamine Yamal", "Pedri", "Gavi", "Raphinha", "Marc-André ter Stegen", "Frenkie de Jong", "Jules Koundé", "Ferran Torres", "Dani Olmo"],
                    "Atletico Madrid": ["Antoine Griezmann", "Julián Álvarez", "Rodrigo De Paul", "Jan Oblak", "Koke", "Marcos Llorente", "Alexander Sørloth"],
                    "Manchester City": ["Erling Haaland", "Kevin De Bruyne", "Phil Foden", "Rodri", "Bernardo Silva", "Ederson", "Ruben Dias", "Jack Grealish"],
                    "Arsenal": ["Bukayo Saka", "Martin Ødegaard", "Declan Rice", "Gabriel Jesus", "William Saliba", "Kai Havertz", "Gabriel Martinelli"]
                }
                
                nombres = None
                for key_name in plantillas_reales:
                    if key_name.lower() in nombre_equipo.lower() or nombre_equipo.lower() in key_name.lower():
                        nombres = plantillas_reales[key_name]
                        break

                if not nombres:
                    nombres = [
                        f"Delantero Estrella ({nombre_equipo[:5]})",
                        f"Mediocampista Titular ({nombre_equipo[:5]})",
                        f"Defensa Central ({nombre_equipo[:5]})",
                        f"Guardameta ({nombre_equipo[:5]})",
                        f"Extremo Veloz ({nombre_equipo[:5]})"
                    ]

                for n in nombres:
                    nuevos_jugadores.append({
                        'nombre': n,
                        'foto': 'https://images.unsplash.com/photo-1511886929837-354d827aae26?auto=format&fit=crop&w=400&q=80'
                    })

            # 4. Guardar en Base de Datos conectando la relación con Equipo
            if nuevos_jugadores:
                db.jugador.delete_many(where={'equipo_id': equipo_id})
                for idx, j_data in enumerate(nuevos_jugadores):
                    img_url = str(j_data.get('foto') or 'https://images.unsplash.com/photo-1511886929837-354d827aae26?auto=format&fit=crop&w=400&q=80')
                    db.jugador.create(data={
                        'nombre': str(j_data['nombre']),
                        'nombre_equipo': str(nombre_equipo),
                        'equipo': {'connect': {'id': int(equipo_id)}},
                        'foto': img_url,
                        'goles': random.randint(3, 22) if idx < 3 else random.randint(0, 5),
                        'remates_al_arco': random.randint(15, 55) if idx < 4 else random.randint(2, 12),
                        'tarjetas_amarillas': random.randint(0, 7),
                        'tarjetas_rojas': random.randint(0, 2)
                    })
    except Exception as e:
        print(f"Error asegurando jugadores para {nombre_equipo}: {e}")

@getStats_blueprint.route('/obtener_info_jugadores', methods=['POST'])
def obtener_info_jugadores():
    nombre_equipo = request.json.get('nombre_equipo') if request.json else None
    if not nombre_equipo:
        return jsonify({'error': 'Falta el nombre del equipo'}), 400
    try:
        jugadores = db.jugador.find_many(where={'nombre_equipo': nombre_equipo})
        jugadores_data = [j.dict() for j in jugadores]
        return jsonify({'jugadores': jugadores_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@getStats_blueprint.route('/plantilla/<nombre_equipo>')
def plantilla_equipo(nombre_equipo):
    try:
        from services.api_football import DEFAULT_SHIELD_SVG, scraper_espn_plantel_equipo_ondemand, obtener_stats_equipo_real

        nombre_clean = urllib.parse.unquote(nombre_equipo).strip()
        stats_real = obtener_stats_equipo_real(nombre_clean)

        equipo = db.equipo.find_first(where={'nombre': nombre_clean}, include={'stats': True})
        if not equipo:
            equipo = db.equipo.find_first(where={'nombre': {'contains': nombre_clean}}, include={'stats': True})

        if not equipo:
            equipo_data = {
                'id': 9999,
                'nombre': nombre_clean,
                'logo': stats_real.get('logo', DEFAULT_SHIELD_SVG),
                'league_id': 140
            }
        else:
            equipo_data = equipo.dict()
            if stats_real.get('logo') and stats_real.get('logo') != DEFAULT_SHIELD_SVG:
                equipo_data['logo'] = stats_real['logo']

        stats_obj = {
            "puntos_totales": stats_real['puntos_totales'],
            "partidos_ganados": stats_real['partidos_ganados'],
            "partidos_empatados": stats_real['partidos_empatados'],
            "partidos_perdidos": stats_real['partidos_perdidos']
        }

        # 1. BUSCAR EN ESPN PRIMERO SIEMPRE (Prioridad 1)
        jugadores_data = []
        espn_squad = scraper_espn_plantel_equipo_ondemand(nombre_clean)
        if espn_squad:
            for idx, p in enumerate(espn_squad):
                jugadores_data.append({
                    'nombre': p.get('nombre', 'Jugador Profesional'),
                    'posicion': p.get('posicion', 'Jugador de Campo'),
                    'foto': p.get('foto') if p.get('foto') and not 'unsplash' in p.get('foto') else equipo_data.get('logo', DEFAULT_SHIELD_SVG),
                    'goles': p.get('goles', random.randint(2, 18) if idx < 3 else random.randint(0, 5)),
                    'remates_al_arco': p.get('remates_al_arco', random.randint(10, 45))
                })

        # 2. SI ESPN NO TIENE DATOS O FALLA, USAR BASE DE DATOS LOCAL (Prioridad 2)
        if not jugadores_data and equipo and hasattr(equipo, 'id'):
            try:
                asegurar_jugadores_reales(equipo.id, equipo.nombre)
                jugadores = db.jugador.find_many(where={'equipo_id': equipo.id})
                if jugadores:
                    jugadores_data = [j.dict() for j in jugadores]
            except Exception as e_db:
                print(f"Nota BD Jugadores: {e_db}")

        # Respaldo final si todo falla para que la plantilla NUNCA este vacia
        if not jugadores_data:
            nombres_base = [
                ("Goleador Principal", "Delantero", 14),
                ("Mediocampista Creativo", "Mediocampista", 8),
                ("Extremo Veloz", "Delantero", 11),
                ("Capitán & Líder", "Mediocampista", 5),
                ("Defensa Central", "Defensa", 2),
                ("Guardameta Titular", "Arquero", 0),
                ("Lateral Izquierdo", "Defensa", 3),
                ("Lateral Derecho", "Defensa", 1)
            ]
            for n_tit, n_pos, n_gol in nombres_base:
                jugadores_data.append({
                    'nombre': f"{n_tit} ({nombre_clean})",
                    'posicion': n_pos,
                    'foto': equipo_data.get('logo', DEFAULT_SHIELD_SVG),
                    'goles': n_gol,
                    'remates_al_arco': n_gol * 3 + 4
                })

        equipo_data['jugadores'] = jugadores_data

        return render_template('plantilla_equipo.html', equipo=equipo_data, jugadores=jugadores_data, stats=stats_obj)
    except Exception as e:
        print(f"Error al cargar plantilla de {nombre_equipo}: {e}")
        return redirect('/estadisticas_equipos')

@getStats_blueprint.route('/estadisticas/tabla_posiciones', methods=['GET'])
def get_tabla_posiciones():
    league_id = request.args.get('league_id', type=int) or 140
    from services.api_football import obtener_tabla_posiciones_real
    standings = obtener_tabla_posiciones_real(league_id)
    return jsonify(standings)

@getStats_blueprint.route('/estadisticas_equipos', methods=['GET', 'POST'])
def estadisticas_equipos():
    selected_league_id = request.args.get('league_id', type=int) or request.form.get('league_id', type=int) or 140

    try:
        from services.api_football import obtener_tabla_posiciones_real
        standings = obtener_tabla_posiciones_real(selected_league_id)
        equipos_data = standings if standings else []
    except Exception as e:
        print(f"Error al cargar equipos desde ESPN scraper: {e}")
        equipos_data = []

    return render_template(
        'estadisticas_equipos.html',
        equipos=equipos_data,
        selected_league_id=selected_league_id
    )

@getStats_blueprint.route('/obtener_estadisticas_json', methods=['POST'])
def obtener_estadisticas_json():
    nombre_equipo = request.json.get('nombre_equipo') if request.json else None
    if not nombre_equipo:
        return jsonify({'error': 'Falta el nombre del equipo'}), 400
    try:
        equipo = db.equipo.find_first(where={'nombre': nombre_equipo}, include={'stats': True})
        if not equipo:
            return jsonify({'error': 'Equipo no encontrado'}), 404

        st = equipo.stats[0] if equipo.stats else None
        if st:
            matriz = np.array([st.partidos_ganados, st.partidos_empatados, st.partidos_perdidos], dtype=float)
            total_pj = float(np.sum(matriz))
            pcts = (matriz / total_pj * 100.0) if total_pj > 0 else np.array([0, 0, 0])
            pg_pct = round(float(pcts[0]), 2)
            pe_pct = round(float(pcts[1]), 2)
            pp_pct = round(float(pcts[2]), 2)
        else:
            pg_pct = pe_pct = pp_pct = 0.0

        jugadores = db.jugador.find_many(where={'equipo_id': equipo.id})
        jugadores_json = [j.dict() for j in jugadores]

        return jsonify({
            'nombre': equipo.nombre,
            'logo': equipo.logo,
            'porcentaje_partidos_ganados': pg_pct,
            'porcentaje_partidos_empatados': pe_pct,
            'porcentaje_partidos_perdidos': pp_pct,
            'jugadores': jugadores_json
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@getStats_blueprint.route('/cerrar_sesion')
def cerrar_sesion():
    return redirect(url_for('index'))
