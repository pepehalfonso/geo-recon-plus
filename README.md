# GeoRecon+

Reescritura moderna de [geo-recon](https://github.com/radioactivetobi/geo-recon): geolocalización
y reputación de IPs desde la terminal y desde el móvil.

```
geo-recon-plus/
├── georecon/          # paquete Python (CLI)
├── tests/             # 84 tests pytest, sin red
├── mobile/            # app Flutter (APK Android)
│   └── build/app/outputs/flutter-apk/app-release.apk
├── tools/             # generador del icono de launcher
└── pyproject.toml
```

## Instalación (CLI)

```bash
cd geo-recon-plus
pip install -e .          # instala el comando `georecon`
pip install -e ".[dev]"   # + pytest, ruff y mypy
```

Requisitos: Python 3.10+ y `requests`.

## Uso

```bash
georecon 8.8.8.8                 # geolocalización + reputación
georecon example.com             # dominios: se resuelven y se busca la IP
georecon 8.8.8.8 1.1.1.1         # varios objetivos en una sola ejecución
georecon --file targets.txt      # objetivos desde un archivo ('-' = stdin)
georecon me                      # tu IP pública
georecon 1.1.1.1 --json          # salida JSON para scripts
georecon 8.8.8.8 --no-reputation # solo geolocalización
georecon 1.1.1.1 --map           # enlace a OpenStreetMap
georecon 1.1.1.1 --open-map      # el mismo enlace, abierto en el navegador
georecon --selftest              # comprueba que cada proveedor responde
georecon 8.8.8.8 --nmap          # añade escaneo nmap (si está instalado)
georecon 8.8.8.8 --nmap-args -sV -O   # argumentos extra para nmap
georecon 8.8.8.8 --retries 4     # tolerancia a redes inestables
NO_COLOR=1 georecon 8.8.8.8      # sin colores
```

Ejemplo real:

```
$ georecon one.one.one.one --no-color

  1.0.0.1
    resolved from one.one.one.one

  Geolocation   [ipwho.is]
    Country       Australia
    Region        Queensland
    City          Brisbane
    Timezone      Australia/Brisbane
    Coordinates   -27.4679, 153.0281
    ASN           AS13335
    Organization  Apnic Research And Development
    ISP           Cloudflare, Inc.
    Domain        cloudflare.com
    Reverse DNS   one.one.one.one

  Reputation   [dnsbl]
    Verdict        CLEAN
    Abuse score    n/a
    - checked 4 DNS blocklists
    - not listed on any checked blocklist
```

### Códigos de salida

| Código | Significado |
| ------ | ----------- |
| 0      | éxito (incluye IPs privadas, que se informan sin consultar nada) |
| 1      | error genérico / sin objetivo |
| 2      | el objetivo no es una IP ni un hostname válido (o no se pudo resolver) |
| 3      | fallo de red, ningún proveedor respondió |
| 4      | el proveedor devolvió un error |
| 5      | `--nmap` pero nmap no está instalado |

En modo lote el programa devuelve 0 solo si todos los objetivos se resolvieron bien; cada
fallo aparece en `errors` con su propio `exit_code`.

### Reputación: con y sin API key

* **Sin key (por defecto):** consulta cuatro listas DNS públicas (Spamhaus ZEN, SpamCop,
  PSBL, Barracudacentral) vía DNS-over-HTTPS. Gratis, sin registro, suficiente para un
  primer filtro. Las respuestas `127.255.255.x` (rate-limit del proveedor) se descartan en
  vez de contar como listado.
* **Con key:** exporta tu propia clave de AbuseIPDB y obtienes el informe completo
  (abuse confidence score, número de reportes, último reporte, whitelist).

```bash
export ABUSEIPDB_KEY="tu-clave"
georecon 203.0.113.10
```

La key **nunca** va dentro del código: si no está en el entorno, la app simplemente usa el
modo sin key. (El repo original tenía una key ajena hardcodeada en `modules/checkIp.py`.)

## Módulo Python

```python
from georecon import lookup

result = lookup("example.com")     # acepta IPs y hostnames
print(result.geo.city, result.connection.isp, result.reputation.verdict)
print(result.to_dict())            # dict listo para JSON
```

## App móvil (APK)

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
flutter build apk --release
# salida: mobile/build/app/outputs/flutter-apk/app-release.apk
```

El APK se instala directamente en Android (minSdk 24 / Android 7.0+). Incluye permiso
`INTERNET`.

Funciones:

* Buscar cualquier IP **o dominio** (se resuelve por DNS-over-HTTPS) o detectar la IP propia.
* Tarjetas de geolocalización, red (ASN, ISP, reverse DNS) y reputación con veredicto
  codificado por color.
* **Abrir en el mapa** (OpenStreetMap) cuando hay coordenadas.
* **Actualizar deslizando** en la pantalla de inicio y de resultados.
* Interfaz en inglés y español, según el idioma del dispositivo (`gen_l10n`).
* Historial de búsquedas persistente.
* Configuración de API key de AbuseIPDB desde la app (se guarda en `SharedPreferences`).
* Copiar la IP o el informe completo en JSON al portapapeles.
* Icono de launcher adaptativo propio (`tools/generate_icon.py`).

## Tests y calidad

```bash
pytest                     # 84 tests, sin red
ruff check .               # lint
mypy                       # tipos (solo georecon/)
cd mobile && flutter test  # 9 tests (7 de red en vivo + 2 widget)
cd mobile && flutter analyze
```

Los tests de Dart de `test/api_service_test.dart` sí tocan la red: validan que el flujo real
(ipwho.is → reverse DNS → blocklists → AbuseIPDB con key inválida) se comporta como se
espera.

En GitHub Actions (`.github/workflows/ci.yml`) se ejecuta todo esto en cada push:
ruff + mypy + pytest (Python 3.10 y 3.12) y analyze + test + build del APK.

## Fuentes de datos

| Uso | Fuente | Key |
| --- | ------ | --- |
| Geolocalización, ASN, ISP | `ipwho.is` | no |
| IP propia (fallback) | `ipify.org` | no |
| DNS (hostnames, reverse) | DNS-over-HTTPS (`dns.google`) | no |
| Reputación básica | Spamhaus / SpamCop / PSBL / Barracudacentral | no |
| Reputación completa | `api.abuseipdb.com` | sí (opcional) |
| Escaneo de puertos | nmap local | no |

## Diferencias con el repo original

* Se puede clonar en Windows (el original tiene archivos con `\r` en el nombre y rompe `git clone`).
* Ninguna API key en el repositorio.
* IP privadas, de documentación o inválidas informan un error claro en vez de `KeyError`.
* Sin `sudo apt install` automático: si falta nmap, lo dice y sale con código 5.
* Multiplataforma: no usa `clear`/`sh`, detecta `NO_COLOR` y no revienta con emojis en consolas antiguas.
* Sin dependencias de Bash; `--json` para automatización, lotes de objetivos y `--selftest`.

## Licencia

MIT — ver [LICENSE](LICENSE).
