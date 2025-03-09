# Maven Mirror Proxy

Este proyecto es un proxy de Maven que permite descargar artefactos de Maven desde un servidor local.

## Requisitos

- Python 3.x
- Requests
- tqdm

## Uso

1. Descarga el código del proyecto.
2. Ejecuta el archivo `run-server.py` para iniciar el servidor.

## Configuración

1. (opcional) Modifica la ruta de descarga en el archivo `run-server.py`.

2. Modifica los archivos de configuracion de gradle en el directorio `android/app/build.gradlew`.
```gradle
allprojects {
    repositories {
        // Repositorio en tu servidor local
        maven {
            url = uri("http://127.0.0.1:8000/repositorio-local")
            content {
                includeGroup("org.jetbrains.kotlin")
                includeGroup("org.jetbrains.kotlin.multiplatform")
            }

            allowInsecureProtocol = true

        }
        }
}
```
