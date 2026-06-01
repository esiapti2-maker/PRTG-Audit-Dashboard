import http.server
import socketserver
import json
import urllib.parse
import asyncio
import aiohttp
import webbrowser
import os
import sys
from datetime import datetime

PORT = 5000
SEMAPHORE_LIMIT = 25

class PRTGAuditHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Maneja las peticiones de CORS preflight."""
        self.send_response(200, "OK")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        # Servir el archivo dashboard.html para la raíz o /dashboard.html
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path in ["/", "/index.html", "/dashboard.html"]:
            self.serve_static_file("dashboard.html", "text/html")
        elif path == "/api/status":
            self.send_json_response({"status": "running", "time": datetime.now().isoformat()})
        else:
            self.send_error(404, "Archivo no encontrado")

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == "/api/audit":
            # Leer el cuerpo de la petición POST
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                params = json.loads(post_data.decode('utf-8'))
            except Exception as e:
                self.send_error_response(400, f"JSON inválido: {str(e)}")
                return

            host = params.get("host")
            username = params.get("username")
            passhash = params.get("passhash")
            password = params.get("password")
            group_id = params.get("group_id")
            if group_id is not None:
                group_id = str(group_id).strip()
            else:
                group_id = ""

            if not host or not username or (not passhash and not password):
                self.send_error_response(400, "Faltan parámetros obligatorios: host, username y (passhash o password)")
                return

            print(f"[*] Iniciando auditoría asíncrona para: {host} (Usuario: {username}, Grupo ID: {group_id if group_id else 'General/Global (Toda la instancia)'})")
            
            try:
                # Correr el bucle asíncrono para esta petición de forma síncrona
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resultados = loop.run_until_complete(
                    self.ejecutar_auditoria_async(host, username, passhash, password, group_id)
                )
                loop.close()
                
                # Intentar guardar una copia CSV local en segundo plano para el historial físico
                try:
                    self.guardar_csv_local(resultados["sensors"], resultados["triggers"], group_id)
                except Exception as ex:
                    print(f"[-] Advertencia al guardar el CSV de respaldo: {ex}")

                self.send_json_response({
                    "success": True,
                    "data": resultados
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_error_response(500, f"Error durante la auditoría: {str(e)}")
        else:
            self.send_error(404, "API endpoint no encontrado")

    def serve_static_file(self, filename, content_type):
        """Sirve un archivo estático desde la carpeta local."""
        try:
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            if not os.path.exists(filepath):
                self.send_error(404, f"Archivo no encontrado: {filename}")
                return

            with open(filepath, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(content))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error interno: {str(e)}")

    def send_json_response(self, data):
        """Envía una respuesta JSON limpia con cabeceras CORS."""
        try:
            content = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", len(content))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"[-] Error enviando respuesta JSON: {e}")

    def send_error_response(self, code, message):
        """Envía un error en formato JSON."""
        self.send_json_response({
            "success": False,
            "error": message
        })

    # ==========================================
    # MOTOR DE EXTRACCIÓN ASÍNCRONO (MIGRADO DE report.py)
    # ==========================================
    async def ejecutar_auditoria_async(self, host, username, passhash, password, group_id):
        sem = asyncio.Semaphore(SEMAPHORE_LIMIT)
        url_base = f"{host.rstrip('/')}/api/table.json"
        prop_url = f"{host.rstrip('/')}/api/getobjectproperty.htm"

        # Construir parámetros comunes de autenticación
        auth_params = {"username": username}
        if passhash:
            auth_params["passhash"] = passhash
        elif password:
            auth_params["password"] = password

        async with aiohttp.ClientSession() as session:
            # 1. Ejecutar en paralelo consultas generales de Dispositivos, Sensores, Triggers, Usuarios y Notificaciones
            # 1.1 Params de Dispositivos
            params_devices = {
                "content": "devices",
                "output": "json",
                "columns": "objid,device,host",
                **auth_params
            }
            if group_id and group_id != "0":
                params_devices["id"] = group_id

            # 1.2 Params de Sensores
            params_sensors = {
                "content": "sensors",
                "output": "json",
                "columns": "objid,group,device,sensor,status,message,lastvalue",
                **auth_params
            }
            if group_id and group_id != "0":
                params_sensors["id"] = group_id

            # 1.3 Params de Triggers
            params_triggers = {
                "content": "triggers",
                "output": "json",
                **auth_params
            }
            if group_id and group_id != "0":
                params_triggers["id"] = group_id

            # 1.4 Params de Usuarios (Global)
            params_users = {
                "content": "users",
                "output": "json",
                "columns": "objid,name,email,type",
                **auth_params
            }

            # 1.5 Params de Notificaciones (Global)
            params_notifications = {
                "content": "notifications",
                "output": "json",
                "columns": "objid,name,active",
                **auth_params
            }

            # Definición de tareas concurrentes de primer nivel
            async def fetch_api(params):
                try:
                    async with session.get(url_base, params=params, ssl=False) as response:
                        if response.status == 200:
                            datos = await response.json()
                            return datos.get(params['content'], datos.get('triggers', []))
                except Exception as err:
                    print(f"[-] Error en llamada API ({params.get('content')}): {err}")
                return []

            print("[*] Lanzando peticiones concurrentes iniciales a PRTG...")
            tareas = [
                fetch_api(params_devices),
                fetch_api(params_sensors),
                fetch_api(params_triggers),
                fetch_api(params_users),
                fetch_api(params_notifications)
            ]
            
            resultados = await asyncio.gather(*tareas)
            
            lista_dispositivos = resultados[0]
            lista_sensores = resultados[1]
            lista_triggers = resultados[2]
            lista_usuarios = resultados[3]
            lista_notificaciones = resultados[4]

            print(f"[+] Datos base cargados: {len(lista_dispositivos)} dispositivos, {len(lista_sensores)} sensores, {len(lista_usuarios)} usuarios.")

            diccionario_ips = {dev.get("device", "").strip(): dev.get("host", "Sin IP") for dev in lista_dispositivos}

            # ==========================================
            # ANÁLISIS DE CANALES Y LÍMITES EN PARALELO
            # ==========================================
            async def fetch_channels_for_sensor(sensor_id):
                params = {
                    "content": "channels",
                    "output": "json",
                    "id": sensor_id,
                    "columns": "name,objid",
                    **auth_params
                }
                async with sem:
                    try:
                        async with session.get(url_base, params=params, ssl=False) as resp:
                            if resp.status == 200:
                                datos = await resp.json()
                                return datos.get("channels", [])
                    except Exception as ex:
                        pass
                return []

            async def fetch_channel_property(sensor_id, subid, prop_name):
                params = {
                    "id": sensor_id,
                    "subtype": "channel",
                    "subid": subid,
                    "name": prop_name,
                    "show": "nohtmlencode",
                    **auth_params
                }
                async with sem:
                    try:
                        async with session.get(prop_url, params=params, ssl=False) as resp:
                            if resp.status == 200:
                                text = await resp.text()
                                # Extraer del tag <result>
                                start = text.find("<result>")
                                if start == -1: return ""
                                start += len("<result>")
                                end = text.find("</result>", start)
                                if end == -1: return ""
                                return text[start:end].strip()
                    except Exception:
                        pass
                return ""

            async def procesar_limites_canal(sensor_id, channel):
                subid = channel.get("objid")
                ch_name = channel.get("name")
                
                limitmode = await fetch_channel_property(sensor_id, subid, "limitmode")
                if limitmode == "1":
                    prop_tareas = [
                        fetch_channel_property(sensor_id, subid, "limitminerror"),
                        fetch_channel_property(sensor_id, subid, "limitminwarning"),
                        fetch_channel_property(sensor_id, subid, "limitmaxerror"),
                        fetch_channel_property(sensor_id, subid, "limitmaxwarning")
                    ]
                    raw_resultados = await asyncio.gather(*prop_tareas)
                    resultados_prop = [r if r != "Not found" else "" for r in raw_resultados]
                    
                    return {
                        "Canal": ch_name,
                        "Limites_Activos": "Sí",
                        "Min_Error": resultados_prop[0],
                        "Min_Warning": resultados_prop[1],
                        "Max_Error": resultados_prop[2],
                        "Max_Warning": resultados_prop[3]
                    }
                return None

            print("[*] Obteniendo canales de todos los sensores en paralelo...")
            canales_tasks = [fetch_channels_for_sensor(s.get("objid")) for s in lista_sensores]
            canales_resultados = await asyncio.gather(*canales_tasks)
            sensor_canales = {s.get("objid"): canales for s, canales in zip(lista_sensores, canales_resultados)}

            print("[*] Analizando propiedades de límites de canales en paralelo...")
            limites_tasks = []
            task_mapping = [] # Asocia la tarea al sensor_id
            
            for s in lista_sensores:
                s_id = s.get("objid")
                for ch in sensor_canales.get(s_id, []):
                    if ch.get("name") == "Downtime":
                        continue
                    task = procesar_limites_canal(s_id, ch)
                    limites_tasks.append(task)
                    task_mapping.append(s_id)
                    
            limites_resultados = await asyncio.gather(*limites_tasks)
            
            # Consolidar los límites activos
            sensor_limites_activos = {}
            for s_id, limit_info in zip(task_mapping, limites_resultados):
                if limit_info:
                    if s_id not in sensor_limites_activos:
                        sensor_limites_activos[s_id] = []
                    sensor_limites_activos[s_id].append(limit_info)

            # ==========================================
            # CRUCE DE DATOS FINAL Y NORMALIZACIÓN PARA DASHBOARD
            # ==========================================
            sensores_finales = []
            sensores_sin_umbrales = []

            for sensor in lista_sensores:
                s_id = sensor.get("objid")
                nombre_equipo = sensor.get("device", "").strip()
                limites_del_sensor = sensor_limites_activos.get(s_id, [])
                
                # Clasificar estado para el badge del frontend
                st = sensor.get("status", "").lower()
                status_mapped = "up"
                if "down" in st:
                    status_mapped = "down"
                elif "warning" in st:
                    status_mapped = "warning"
                elif "paused" in st:
                    status_mapped = "paused"

                # Guardamos sensor básico para tabla principal
                sensor_info = {
                    "id": s_id,
                    "name": sensor.get("sensor", ""),
                    "device": nombre_equipo,
                    "group": sensor.get("group", ""),
                    "status": status_mapped,
                    "lastvalue": sensor.get("lastvalue", ""),
                    "message": sensor.get("message", "")
                }
                sensores_finales.append(sensor_info)

                 # Si no tiene límites activos, se agrega a hallazgos de "sin umbral"
                if not limites_del_sensor:
                    sensores_sin_umbrales.append({
                        "id": s_id,
                        "name": sensor.get("sensor", ""),
                        "device": nombre_equipo,
                        "group": sensor.get("group", ""),
                        "lastvalue": sensor.get("lastvalue", ""),
                        "limitmode": "0" # Inactivo
                    })
                else:
                    # Si tiene límites, adjuntar detalles informativos
                    sensor_info["limits"] = limites_del_sensor

            # Clasificación de riesgo de usuarios para el dashboard
            usuarios_finales = []
            for u in lista_usuarios:
                tipo = u.get("type", "User")
                nombre = u.get("name", "")
                
                # Heurística de Riesgo
                if "admin" in nombre.lower() or tipo.lower() == "administrator":
                    riesgo = "Alto"
                elif "read" in tipo.lower() or "ro" in nombre.lower():
                    riesgo = "Bajo"
                else:
                    riesgo = "Medio"

                usuarios_finales.append({
                    "name": nombre,
                    "email": u.get("email", ""),
                    "type": tipo,
                    "risk": riesgo
                })

            # Clasificación de notificaciones
            notificaciones_finales = []
            for n in lista_notificaciones:
                activa = str(n.get("active", "")).strip() == "1"
                
                # Buscar si esta notificación tiene algún trigger asociado en lista_triggers
                # Los triggers se asocian típicamente usando el ID de la plantilla
                n_id = str(n.get("objid", ""))
                has_trigger = False
                trigger_desc = "Sin disparador configurado"
                
                for t in lista_triggers:
                    # Comprobar si el ID de notificación coincide con el destino del trigger
                    if str(t.get("onnotificationid")) == n_id:
                        has_trigger = True
                        trigger_desc = t.get("condition", "Configurado")
                        break

                finding = "Correcta"
                if not activa:
                    finding = "Inactiva — revisar"
                elif not has_trigger:
                    finding = "Huérfana (sin trigger)"

                notificaciones_finales.append({
                    "name": n.get("name", ""),
                    "active": activa,
                    "trigger": trigger_desc,
                    "finding": finding
                })

            return {
                "devices": len(lista_dispositivos),
                "sensors": sensores_finales,
                "noLimits": sensores_sin_umbrales,
                "users": usuarios_finales,
                "notifications": notificaciones_finales,
                "triggers": [{
                    "condition": t.get("condition", ""),
                    "onnotificationid": t.get("onnotificationid", "")
                } for t in lista_triggers]
            }

    def guardar_csv_local(self, sensores, triggers, group_id):
        """Exporta un reporte CSV con timestamp localmente en el servidor para control histórico."""
        fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        grp_label = group_id if group_id else "General"
        nombre_archivo = f"Auditoria_Sensores_{grp_label}_{fecha_hora}.csv"
        
        # Crear carpeta de reportes si no existe
        reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reportes_historicos")
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        filepath = os.path.join(reports_dir, nombre_archivo)
        
        import csv
        with open(filepath, mode='w', newline='', encoding='utf-8-sig') as f:
            escritor = csv.writer(f)
            # Cabecera
            escritor.writerow(["ID Sensor", "Sensor", "Dispositivo", "Grupo", "Estado", "Último Valor", "Mensaje", "Límites Configurados"])
            
            for s in sensores:
                lims_desc = ""
                if "limits" in s:
                    lims_desc = "; ".join([f"{l['Canal']}(MinErr:{l['Min_Error']}, MaxErr:{l['Max_Error']})" for l in s["limits"]])
                else:
                    lims_desc = "Ninguno"

                escritor.writerow([
                    s.get("id"),
                    s.get("name"),
                    s.get("device"),
                    s.get("group"),
                    s.get("status"),
                    s.get("lastvalue"),
                    s.get("message"),
                    lims_desc
                ])
        print(f"[+] Historial físico guardado localmente como: {filepath}")

def run_server():
    # Asegurar que el servidor se pueda reiniciar liberando el socket rápidamente
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), PRTGAuditHandler) as httpd:
        print("=========================================================================")
        print(f"   PRTG AUDIT INTEGRATED TOOL - SERVIDOR INICIADO EN PUERTO {PORT}")
        print("=========================================================================")
        print(f"   [+] Dashboard Web local: http://localhost:{PORT}/")
        print(f"   [+] Endpoint de auditoría asíncrona: http://localhost:{PORT}/api/audit")
        print("=========================================================================")
        print("   Para cerrar el servidor, presiona CTRL+C en esta terminal.")
        print("=========================================================================")
        
        # Abrir el navegador por defecto automáticamente
        try:
            webbrowser.open(f"http://localhost:{PORT}/")
        except Exception as e:
            print(f"[-] No se pudo abrir el navegador automáticamente: {e}")
            
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[-] Apagando el servidor local...")
            sys.exit(0)

if __name__ == "__main__":
    run_server()
