import os
import requests
from tqdm import tqdm
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# Ruta base para los archivos locales
REMOTE_REPO = "https://repo.maven.apache.org/maven2"
print("MAVEN MIRROR PROXY")
class RequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Ruta de solicitud
        requested_path = self.path.strip('/')
        local_path = os.path.join(requested_path)
        requested_path = requested_path.replace("repositorio-local", "")
        print(f"[ + ] Solicitando archivo: {requested_path}")
        print(f"[ + ] Ruta local: {local_path}")
        print(f"[ + ] Ruta remota: {REMOTE_REPO}{requested_path}")

        # Si el archivo existe en el servidor local
        if os.path.exists(local_path):
            print(f"[ + ] Sirviendo archivo localmente: {self.path}")
            super().do_GET()
        else:
            # Si no, descargamos el archivo desde el repositorio remoto
            self.download_and_serve(requested_path, local_path)

    def download_and_serve(self, requested_path, local_file_path):
        remote_url = f"{REMOTE_REPO}{requested_path}"
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

        # Verificar si el archivo existe antes de intentar descargarlo
        if not self.check_file_exists(remote_url):
            print(f"[ - ] Archivo no encontrado en el repositorio remoto: {remote_url}")
            self.send_error(404, "Archivo no encontrado en el repositorio remoto.")
            return

        # Descargar el archivo remoto
        print(f"[   ] Descargando: {remote_url}")
        self.retry_download(remote_url, local_file_path)

    def check_file_exists(self, remote_url):
        try:
            response = requests.head(remote_url)
            return response.status_code == 200
        except Exception as e:
            print(f"[ - ] Error al verificar la existencia del archivo: {e}")
            return False

    def retry_download(self, remote_url, local_file_path):
        max_retries = 5  # Máximo número de reintentos
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Intentar descargar el archivo
                self.download_file(remote_url, local_file_path)
                break  # Si la descarga fue exitosa, salimos del bucle
            except Exception as e:
                retry_count += 1
                print(f"[ - ] Error en la descarga: {e}. Reintentando... ({retry_count}/{max_retries})")
                if retry_count == max_retries:
                    print("[ - ] Se alcanzó el máximo número de reintentos. No se pudo descargar el archivo.")
                    self.send_error(404, "No se pudo descargar el archivo después de varios intentos.")
                else:
                    continue

    def download_file(self, remote_url, local_file_path):
        # Verificamos si ya existe un archivo parcialmente descargado
        file_size = os.path.exists(local_file_path) and os.path.getsize(local_file_path) or 0

        # Realizamos la solicitud con el encabezado "Range" para reanudar la descarga
        headers = {'Range': f"bytes={file_size}-"} if file_size > 0 else {}
        response = requests.get(remote_url, headers=headers, stream=True)

        if response.status_code == 200 or response.status_code == 206:  # 206 es para "Partial Content"
            total_size = int(response.headers.get('content-length', 0)) + file_size
            chunk_size = 1024  # Tamaño de bloque (1 KB)

            # Usamos tqdm para mostrar el progreso de la descarga
            with open(local_file_path, 'ab') as f, tqdm(
                desc="Downloading",
                total=total_size,
                initial=file_size,
                unit='B',
                unit_scale=True,
                ncols=100
            ) as bar:
                # Descargamos en fragmentos (chunks)
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
            print(f"[ + ] Archivo descargado y guardado en: {local_file_path}")

            # Después de la descarga, servimos el archivo localmente
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Content-Length", os.path.getsize(local_file_path))  # Usamos el tamaño real del archivo
            self.end_headers()

            # Aseguramos que no tratemos de consumir la respuesta nuevamente
            with open(local_file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            print(f"[ - ] Error al descargar el archivo: {response.status_code}")
            self.send_error(404, f"Archivo no encontrado: {remote_url}")

# Definir el servidor que servirá múltiples solicitudes en hilos
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def run_server(port=8000):
    handler = RequestHandler
    server = ThreadedHTTPServer(('0.0.0.0', port), handler)
    print(f"Servidor HTTP en http://0.0.0.0:{port}")
    server.serve_forever()

if __name__ == "__main__":
    # Iniciar el servidor HTTP en el puerto 8000 por defecto
    run_server(8000)
