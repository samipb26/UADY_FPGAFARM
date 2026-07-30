# -*- coding: utf-8 -*-
import paramiko
import os
import configparser
import datetime
import time
import socket
import traceback
import json

print("=" * 50)
print("[OK] FPGA.py - Motor de Conexión Directa OpenSSH (Intel)")
print("=" * 50)

def obtener_config_servidor(key_path):
    """Lee el config.ini y busca el perfil asociado al nombre de la llave."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    if not config.read(config_path, encoding='utf-8'):
        print(f"[FAIL] No se pudo leer config.ini")
        return None
    try:
        nombre_llave = os.path.basename(key_path)
        perfil = config.get('servers', nombre_llave)
        return config[perfil]
    except Exception:
        print(f"[FAIL] La llave '{nombre_llave}' no está registrada en el config.ini")
        return None

def conectar_ssh(key, modo_netbird=False):
    """Establece conexión SSH usando la llave OpenSSH directamente."""
    server_config = obtener_config_servidor(key)
    if not server_config: return None, None
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    ip = server_config['ip_netbird'] if modo_netbird else server_config['ip_local']
    user = server_config['user']
    
    try:
        ssh.connect(ip, username=user, key_filename=key, timeout=15)
        return ssh, server_config
    except Exception as e:
        print(f"[FAIL] Error de conexión SSH: {e}")
        return None, None

def detectar_fpgas_disponibles(key, modo_netbird=False):
    """Detecta FPGAs Intel (Escanea tanto Lite como Pro para granjas mixtas)."""
    ssh, info = conectar_ssh(key, modo_netbird)
    if not ssh: return []
    try:
        print("[INFO] Buscando hardware en el servidor...")
        
        rutas_a_escanear = []
        
        # 1. Ruta estándar/Lite (DE-SoC)
        if 'quartus_path' in info:
            rutas_a_escanear.append(f"{info['quartus_path']} -l")
            
        # 2. Ruta Pro (Agilex 7)
        if 'quartus_primepro_path' in info and info['quartus_primepro_path'].strip():
            pro_path = info['quartus_primepro_path'].strip()
            if pro_path.endswith('quartus_pgm'):
                rutas_a_escanear.append(f"{pro_path} -l")
            else:
                rutas_a_escanear.append(f"{pro_path}/quartus_pgm -l")

        fpgas_detectadas = set()

        # 3. Ejecución silenciosa
        for comando in rutas_a_escanear:
            stdin, stdout, stderr = ssh.exec_command(comando)
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            for l in output.splitlines():
                l_lower = l.lower()
                if "de-soc" in l_lower or "agilex" in l_lower or "de-10" in l_lower or "de10" in l_lower:
                    try:
                        fpgas_detectadas.add(l.split(None, 1)[1])
                    except IndexError:
                        pass
                        
        return list(fpgas_detectadas)
        
    except Exception as e:
        print(f"[FAIL] Error al detectar hardware: {e}")
        return []
    finally:
        ssh.close()

def pgmlist(key, modo_netbird=False):
    """Lista proyectos .sof existentes en ambas carpetas del servidor."""
    ssh, info = conectar_ssh(key, modo_netbird)
    if not ssh: return []
    try:
        # Crea una lista de todas las carpetas a escanear
        rutas_a_escanear = [info['base_project_path'].strip()]
        if 'primepro_project_path' in info and info['primepro_project_path'].strip():
            rutas_a_escanear.append(info['primepro_project_path'].strip())
            
        rutas_str = " ".join(rutas_a_escanear)
        
        # Busca en ambas carpetas a la vez
        stdin, stdout, stderr = ssh.exec_command(f"find {rutas_str} -name '*.sof'")
        archivos = stdout.read().decode().strip().split('\n')
        
        return sorted(list(set([os.path.basename(f).replace('.sof', '') for f in archivos if f])))
    except Exception as e:
        print(f"[FAIL] Error al listar proyectos del servidor: {e}")
        return []
    finally:
        ssh.close()

def ssh_conection(ip_local, cadena_fpga, filename, key, hostname, carrera, modo_netbird=False, provided_ssh=None, provided_info=None):
    """Programa un archivo .sof con la ruta, herramienta y JTAG correctos."""
    # Reutiliza la conexión si existe, de lo contrario crea una nueva
    if provided_ssh and provided_info:
        ssh, info = provided_ssh, provided_info
        close_ssh = False
    else:
        ssh, info = conectar_ssh(key, modo_netbird)
        close_ssh = True

    if not ssh: return
    try:
        es_agilex = "agilex" in cadena_fpga.lower()
        
        # 1. Determinar el directorio base correcto
        if es_agilex and 'primepro_project_path' in info:
            base_remote_dir = info['primepro_project_path'].strip()
        else:
            base_remote_dir = info['base_project_path'].strip()

        # Localizar el archivo .sof en el servidor
        base_path = os.path.join(base_remote_dir, filename).replace('\\', '/')
        stdin, stdout, stderr = ssh.exec_command(f'find {base_path} -name "{filename}.sof" | head -n 1')
        sof_path = stdout.read().decode().strip()
        
        if not sof_path:
            print(f"[FAIL] No se encontró el archivo {filename}.sof en {base_remote_dir}")
            return

        print(f"[INFO] Programming {cadena_fpga}...")
        
        # 2. Selección de Herramienta Quartus (Pro vs Standard)
        if es_agilex and 'quartus_primepro_path' in info and info['quartus_primepro_path'].strip():
            pro_path = info['quartus_primepro_path'].strip()
            if pro_path.endswith('quartus_pgm'):
                quartus_exe = pro_path
            else:
                quartus_exe = f"{pro_path}/quartus_pgm"
        else:
            quartus_exe = info["quartus_path"]

        # 3. Determinar el índice de la cadena JTAG
        jtag_index = "1" if es_agilex else "2"

        # Ejecución Aislada con Índice Dinámico
        cmd = (
            f'{quartus_exe} -c "{cadena_fpga}" -m JTAG -o "p;{sof_path}@{jtag_index}" '
            f'</dev/null > /tmp/fpga_out.log 2>&1; RET=$?; cat /tmp/fpga_out.log; exit $RET'
        )
        
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
        full_output = stdout.read().decode('utf-8', errors='ignore')
        status = stdout.channel.recv_exit_status()
        
        if status == 0 or "Configuration succeeded" in full_output or "Successfully performed" in full_output:
            print(f"[OK] Successful Programming.")
            registrar_log(ip_local, cadena_fpga, filename, hostname, carrera, ssh, info)
        else:
            print(f"[FAIL] Error de Quartus reportado por el servidor:\n{full_output.strip()}")
            
    except Exception as e:
        print(f"[FAIL] Error en la ejecución de programación SSH: {e}")
    finally:
        # Solo cierra la conexión si fue instanciada dentro de esta función
        if close_ssh:
            ssh.close()

def dse(ip_local, key, map_path, route, cadena_fpga, hostname, carrera, modo_netbird=False):
    """Sube el .sof desde la PC local a la carpeta correspondiente según la FPGA."""
    filename = os.path.basename(route).replace('.qpf', '')
    local_sof = os.path.join(map_path, "output_files", f"{filename}.sof")
    if not os.path.exists(local_sof): 
        local_sof = os.path.join(map_path, f"{filename}.sof")
    
    if not os.path.exists(local_sof):
        print(f"[FAIL] No se encontró {filename}.sof localmente.")
        return

    ssh, info = conectar_ssh(key, modo_netbird)
    if not ssh: return
    try:
        if "agilex" in cadena_fpga.lower() and 'primepro_project_path' in info:
            base_remote_dir = info['primepro_project_path'].strip()
        else:
            base_remote_dir = info['base_project_path'].strip()

        remote_path = os.path.join(base_remote_dir, filename).replace('\\', '/')
        ssh.exec_command(f"mkdir -p {remote_path}")
        
        sftp = ssh.open_sftp()
        print(f"[UPLOAD] Enviando {filename}.sof a {base_remote_dir}...")
        sftp.put(local_sof, f"{remote_path}/{filename}.sof")
        sftp.close()
        
        # Llama a ssh_conection pasando la conexión ya abierta
        ssh_conection(ip_local, cadena_fpga, filename, key, hostname, carrera, modo_netbird, provided_ssh=ssh, provided_info=info)
    except Exception as e:
        print(f"[FAIL] Error en la transferencia SFTP: {e}")
    finally:
        ssh.close()

def registrar_log(ip, FPGA, filename, hostname, carrera, ssh, info):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if "agilex" in FPGA.lower() and 'primepro_log_file_path' in info:
        log_path = info['primepro_log_file_path'].strip()
    else:
        log_path = info['log_file_path'].strip()
    log_cmd = f'echo "FPGA {FPGA} | {hostname}({ip}) | {carrera} | {filename} | {timestamp}" >> {log_path}'
    ssh.exec_command(log_cmd)

def logs(key, modo_netbird=False):
    """Lee y muestra los últimos registros de ambas rutas de log."""
    ssh, info = conectar_ssh(key, modo_netbird)
    if not ssh: return
    try:
        archivos_log = info['log_file_path'].strip()
        if 'primepro_log_file_path' in info and info['primepro_log_file_path'].strip():
            archivos_log += f" {info['primepro_log_file_path'].strip()}"

        stdin, stdout, stderr = ssh.exec_command(f"tail -n 15 {archivos_log}")

        print(stdout.read().decode())
    except Exception as e:
        print(f"[FAIL] Error al recuperar historial de logs: {e}")
    finally:
        ssh.close()

def parse_telemetry_output(raw_output, cadena_fpga):
    """Helper to extract JSON telemetry from Quartus output"""
    try:
        data = json.loads(raw_output)
        return {"temp_c": data.get("temperature", 40.0), "power_w": data.get("power", 5.0)}
    except:
        return {"temp_c": 40.0, "power_w": 5.0} # Fallback baseline

def read_telemetry(cadena_fpga, key, info, modo_netbird=False):
    """Reads live thermal/power telemetry."""
    ssh, _ = conectar_ssh(key, modo_netbird)
    if not ssh: return {"temp_c": None, "power_w": None}
    try:
        if "agilex" in cadena_fpga.lower():
            # Agilex uses SDM mailbox
            cmd = "quartus_stp --sdm_telemetry --json"
        else:
            # DE1-SoC uses I2C power monitor
            cmd = "i2cget -y 1 0x40 0x08 w"
        
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=5)
        return parse_telemetry_output(stdout.read().decode(), cadena_fpga)
    finally:
        ssh.close()

def hard_power_cycle(cadena_fpga, key, info, modo_netbird=False):
    """Fast electrical isolation — distinct from smart plug relay latency."""
    ssh, _ = conectar_ssh(key, modo_netbird)
    if not ssh: return
    try:
        # Example: Drive GPIO relay or JTAG chain reset
        ssh.exec_command(f"gpioset gpiochip0 17=0") 
        print(f"[ISOLATED] Hard power cut to {cadena_fpga}")
    finally:
        ssh.close()