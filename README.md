# GeoRecon+

Reescritura moderna de [geo-recon](https://github.com/radioactivetobi/geo-recon): geolocalización
y reputación de IPs desde la terminal y desde el móvil.

```
geo-recon-plus/
├── georecon/          # paquete Python (CLI)
├── tests/             # 45 tests pytest, sin red
├── mobile/            # app Flutter (APK Android)
│   └── build/app/outputs/flutter-apk/app-release.apk
└── pyproject.toml
```

## Instalación (CLI)

```bash
cd geo-recon-plus
pip install -e .          # instala el comando `georecon`
pip install -e ".[dev]"   # + pytest
```

Requisitos: Python 3.9+ y `requests`.

## Uso

```bash
georecon 8.8.8.8                 # geolocalización + reputación
georecon me                      # tu IP pública
georecon 1.1.1.1 --json          # salida JSON para scripts
georecon 8.8.8.8 --no-reputation # solo geolocalización
georecon 8.8.8.8 --nmap          # añade escaneo nmap (si está instalado)
georecon 8.8.8.8 --nmap-args -sV -O   # argumentos extra para nmap
NO_COLOR=1 georecon 8.8.8.8      # sin colores
```

Ejemplo real:

```
$ georecon 1.1.1.1 --no-color

  1.1.1.1

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
    - checked 3 DNS blocklists
    - not listed on any checked blocklist
```

### Códigos de salida

| Código | Significado |
| ------ | ----------- |
| 0      | éxito (incluye IPs privadas, que se informan sin consultar nada) |
| 1      | error genérico / sin objetivo |
| 2      | la IP no es válida |
| 3      | fallo de red, ningún proveedor respondió |
| 4      | el proveedor devolvió un error |
| 5      | `--nmap` pero nmap no está instalado |

### Reputación: con y sin API key

* **Sin key (por defecto):** consulta tres listas DNS públicas (Spamhaus ZEN, SpamCop,
  Barracudacentral) vía DNS-over-HTTPS. Gratis, sin registro, suficiente para un primer filtro.
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

result = lookup("8.8.8.8")
print(result.geo.city, result.connection.isp, result.reputation.verdict)
print(result.to_dict())   # dict listo para JSON
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

* Buscar cualquier IP o detectar la IP propia.
* Tarjetas de geolocalización, red (ASN, ISP, reverse DNS) y reputación con veredicto
  codificado por color.
* Historial de búsquedas persistente.
* Configuración de API key de AbuseIPDB desde la app (se guarda en `SharedPreferences`).
* Copiar la IP o el informe completo en JSON al portapapeles.

## Tests

```bash
pytest                     # 45 tests, sin red
cd mobile && flutter test  # 1 widget test + 5 tests de red en vivo
```

Los tests de Dart de `test/api_service_test.dart` sí tocan la red: validan que el flujo real
(ipwho.is → reverse DNS → blocklists → AbuseIPDB con key inválida) se comporta como se espera.

## Fuentes de datos

| Uso | Fuente | Key |
| --- | ------ | --- |
| Geolocalización, ASN, ISP | `ipwho.is` | no |
| IP propia (fallback) | `ipify.org` | no |
| Reverse DNS | DNS-over-HTTPS (`dns.google`) | no |
| Reputación básica | Spamhaus / SpamCop / Barracudacentral | no |
| Reputación completa | `api.abuseipdb.com` | sí (opcional) |
| Escaneo de puertos | nmap local | no |

## Diferencias con el repo original

* Se puede clonar en Windows (el original tiene archivos con `\r` en el nombre y rompe `git clone`).
* Ninguna API key en el repositorio.
* IP privadas, de documentación o inválidas informan un error claro en vez de `KeyError`.
* Sin `sudo apt install` automático: si falta nmap, lo dice y sale con código 5.
* Multiplataforma: no usa `clear`/`sh`, detecta `NO_COLOR` y no revienta con emojis en consolas antiguas.
* Sin dependencias de Bash; `--json` para automatización.
