# Cómo se hace todo: GeoRecon+

Esta guía explica el proyecto por dentro: qué hay en cada carpeta, cómo viaja una
consulta de principio a fin, cómo se compila el APK, cómo se hacen las capturas y
cómo se publica todo en GitHub. Pensada para que cualquiera pueda reproducirlo o
ampliarlo.

Repositorio: <https://github.com/pepehalfonso/geo-recon-plus>
Referencia original: <https://github.com/radioactivetobi/geo-recon>

---

## 1. Visión general

Hay dos aplicaciones que comparten el mismo modelo de datos:

| Pieza | Tecnología | Entrada | Salida |
| ----- | ---------- | ------- | ------ |
| CLI `georecon` | Python 3.10+ (`requests`) | IP, dominio, varios objetivos | texto con color o `--json` |
| App Android | Flutter (Dart) | IP/dominio desde el móvil | tarjetas de geolocalización, red y reputación |

Las dos hacen exactamente lo mismo:

```
objetivo (IP o dominio)
   │  si es dominio → se resuelve con DNS-over-HTTPS (dns.google)
   ▼
ipwho.is        → país, región, ciudad, coordenadas, zona horaria
ipwho.is        → ASN, organización, ISP, dominio inverso
dns.google (PTR)→ reverse DNS
4 DNSBL vía DoH → ¿está listado en Spamhaus / SpamCop / PSBL / Barracudacentral?
AbuseIPDB       → opcional, solo si el usuario aporta su API key
   ▼
veredicto (clean | suspicious | malicious | unknown) + notas
```

Todo es **gratuito y sin registro**: la reputación sin key sale de cuatro listas DNS
públicas consultadas por DoH; la API key de AbuseIPDB es opcional y nunca se guarda
en el código (el repo original traía una key ajena hardcodeada).

---

## 2. Estructura del repositorio

```
geo-recon-plus/
├── georecon/               # paquete Python (la CLI)
│   ├── cli.py              # argparse, bucle principal, impresión (main())
│   ├── lookup.py           # orquesta: validar → geo → reputación → modelo
│   ├── providers.py        # llamadas HTTP: ipwho.is, ipify, DoH, AbuseIPDB, DNSBL
│   ├── resolver.py         # valida IP/dominio y resuelve hostnames (DoH)
│   ├── http.py             # getter con reintentos/backoff y tiempo de espera
│   ├── models.py           # dataclasses GeoInfo, ConnectionInfo, Reputation, Result
│   ├── output.py           # tabla con color y serialización JSON (schema v2)
│   ├── nmap.py             # escaneo opcional con nmap local
│   ├── selftest.py         # `georecon --selftest`
│   └── errors.py           # NetworkError, ProviderError, exit codes
├── tests/                  # 84 tests pytest, sin red
├── mobile/                 # proyecto Flutter
│   ├── lib/
│   │   ├── main.dart               # arranque, tema, locale inyectable
│   │   ├── screens/home_screen.dart      # formulario, historial, diálogo de key
│   │   ├── screens/result_screen.dart    # tarjetas + "Open on map" + pull-to-refresh
│   │   ├── services/api_service.dart     # TODO el lado de red de la app
│   │   ├── models/ip_info.dart           # modelos inmutables de la respuesta
│   │   └── l10n/                         # ARB (en/es) + Dart generado
│   ├── test/               # 9 tests Dart (7 de red en vivo + 2 widget)
│   ├── android/            # Gradle, manifest, firma debug
│   ├── l10n.yaml           # configuración de gen-l10n
│   └── pubspec.yaml        # versión, dependencias, flutter_launcher_icons
├── tools/
│   ├── generate_icon.py            # icono adaptativo con Pillow
│   └── render_cli_screenshot.py    # captura del CLI para la documentación
├── docs/
│   ├── COMO-SE-HACE.md     # este archivo
│   └── screenshots/        # imágenes que usa el README
├── .github/workflows/ci.yml
├── pyproject.toml          # versión, entry point, ruff, mypy, pytest
├── README.md  CHANGELOG.md  LICENSE (MIT)
└── GeoRecon-plus.apk       # artefacto local, ignorado por git
```

---

## 3. La CLI, paso a paso

### 3.1 Ciclo de vida de una consulta

```bash
georecon example.com --retries 3
```

1. **`cli.py`** parsea los argumentos (`targets` con `nargs="*"`, `--file`, `--json`,
   `--map`, `--open-map`, `--no-reputation`, `--nmap`, `--retries`, `--selftest`…).
   Si no hay objetivos, lee de `--file` (o de stdin con `-`).
2. **`resolver.py`** valida cada objetivo: si es IPv4/IPv6 pasa tal cual; si es un
   dominio lo resuelve por DoH (A primero, luego AAAA) y anota `resolved_from` para
   mostrarlo en la salida.
3. Direcciones privadas/de documentación/loopback se detectan con `ipaddress` y se
   informan **sin tocar la red** (código de salida 0).
4. **`providers.geo_lookup`** llama a `https://ipwho.is/{ip}` y normaliza la
   respuesta en `GeoInfo` + `ConnectionInfo`. Si el proveedor falla, se reintenta
   (`http.py`, backoff exponencial) y finalmente se marca como `ProviderError`.
5. **`providers.reverse_dns`** construye el nombre PTR (`in-addr.arpa` /
   `ip6.arpa`) y lo consulta por DoH.
6. **`providers.dnsbl_lookup`** hace la comprobación de reputación (apartado 3.3).
7. Si hay `ABUSEIPDB_KEY` en el entorno, **`providers.abuseipdb_lookup`** pide el
   informe completo y `merge_reputation` combina ambas fuentes: si el DNSBL dice
   `suspicious` y AbuseIPDB dice `clean`, se sube a `suspicious`.
8. **`output.py`** imprime la tabla con colores (respeta `NO_COLOR`) o serializa
   JSON con `schema_version: 2`, `target` y `errors[]` en modo lote.

### 3.2 Reputación sin key (el corazón del proyecto)

Un DNSBL se consulta así: se invierte la IP (`1.2.3.4` → `4.3.2.1`) y se le hace un
`A` a `<invertida>.<zona>`:

```
4.3.2.1.zen.spamhaus.org   → NOERROR + 127.0.0.2  ⇒ listado
4.3.2.1.bl.spamcop.net     → NXDOMAIN              ⇒ limpio
```

Como no se puede hacer DNS crudo en todos los entornos (y mucho menos en Android),
la consulta se empaqueta como JSON en `https://dns.google/resolve?name=…&type=A`.

Dos detalles importantes que arreglan fallos del original:

* **`127.255.255.x` significa "no preguntado más"**: los resolvers públicos limitan
  la tasa y responden eso. Se descarta (`refused`) y **no** cuenta como listado.
* Si una zona no responde, simplemente no se cuenta en `checked`; el informe dice
  `checked 4 DNS blocklists` solo con las que contestaron.

Las cuatro zonas viven en un único sitio por lenguaje:

* Python: `georecon/providers.py` → `DNSBL_ZONES`
* Dart: `mobile/lib/services/api_service.dart` → `_dnsblZones`

### 3.3 Salida y códigos de salida

| Código | Significado |
| ------ | ----------- |
| 0 | éxito (incluye IPs privadas, informadas sin consultar nada) |
| 1 | error genérico / sin objetivo |
| 2 | objetivo inválido o irresoluble |
| 3 | fallo de red, ningún proveedor respondió |
| 4 | el proveedor devolvió un error |
| 5 | `--nmap` sin nmap instalado |

En lote, 0 solo si todos los objetivos fueron bien; cada fallo entra en `errors`
con su propio `exit_code`.

---

## 4. Tests y calidad

La regla es que **los tests de Python nunca toquen la red**. `providers.py` recibe
el callable `get` como parámetro, así que en `tests/conftest.py` hay un `FakeGet`
que devuelve payloads fijos:

```python
def test_dnsbl_counts_only_reachable_zones(fake_get):
    rep = dnsbl_lookup("1.2.3.4", fake_get)   # respuestas predeterminadas
    assert "checked" in rep.notes[0]
```

Comandos de verificación (todo esto está en el CI):

```bash
ruff check .        # lint (E/F/I/UP/B/SIM/C4/RUF/PIE/RET, sin print fuera de cli/tools)
mypy                # tipos, solo georecon/
python -m pytest    # 84 tests
cd mobile && flutter analyze && flutter test   # analyze limpio + 9 tests
```

Los tests de Dart `test/api_service_test.dart` sí usan la red en vivo: validan que
el flujo real (ipwho.is → PTR → blocklists → AbuseIPDB con key inválida) se comporta
como se espera. `widget_test.dart` renderiza el home en inglés y en español
(`GeoReconApp(locale:)`), que es lo que permite inyectar el locale en tests.

---

## 5. La app Android

### 5.1 Arquitectura

Sin state management ni dependencias de UI: `StatefulWidget` + un `ApiService` que
devuelve modelos inmutables (`models/ip_info.dart`).

* `home_screen.dart`: campo de texto, botones *Look up* / *My IP*, historial de
  últimas búsquedas persistido en `SharedPreferences`, diálogo para pegar la API key
  de AbuseIPDB, pull-to-refresh.
* `result_screen.dart`: tarjeta de veredicto (color según `Verdict`), tarjeta de
  geolocalización con botón **Open on map** (`url_launcher` → OpenStreetMap), tarjeta
  de red (ASN/ISP/reverse DNS), avisos (`warnings`), copiar IP / copiar JSON,
  pull-to-refresh que repite la consulta.
* `services/api_service.dart`: casi toda la red. Timeouts de 12–15 s, errores
  tipados (`LookupException`) que la UI traduce a mensajes, y las mismas cuatro
  DNSBL que la CLI.

### 5.2 Localización

`l10n.yaml` + `generate: true` en `pubspec.yaml`. Se editan los ARB
(`lib/l10n/app_en.arb`, `app_es.arb`) y se regenera el Dart:

```bash
cd mobile
flutter gen-l10n     # escribe app_localizations*.dart (están trackeados)
```

La app elige idioma según el sistema; los tests inyectan uno a propósito.

### 5.3 Icono adaptativo

`tools/generate_icon.py` dibuja con Pillow un globo con retícula y escribe
`mobile/assets/icon/icon.png` (1024) y `foreground.png` (432×432 con el motivo
escalado al 92 % del lienzo). Luego:

```bash
dart run flutter_launcher_icons   # genera mipmaps + ic_launcher adaptativo
```

---

## 6. Compilar e instalar el APK

```bash
cd mobile
flutter pub get
flutter build apk --release --split-per-abi
```

Salidas en `mobile/build/app/outputs/flutter-apk/`:

| Archivo | Arquitectura | Tamaño |
| ------- | ------------ | ------ |
| `app-arm64-v8a-release.apk` | casi todos los móviles actuales | ~8,2 MB |
| `app-armeabi-v7a-release.apk` | 32 bits | ~7,7 MB |
| `app-x86_64-release.apk` | emuladores / Intel | ~8,3 MB |

Dos decisiones de tamaño:

* `packaging.jniLibs.useLegacyPackaging = true` en
  `mobile/android/app/build.gradle.kts` → las librerías nativas van **comprimidas**
  dentro del APK. Sin eso Flutter las descomprime y cada APK pasa de ~8 a ~17 MB.
* `--split-per-abi` → un APK por arquitectura en vez de uno gordo de 22 MB (48 MB
  sin comprimir).

Para probar en el emulador (x86_64):

```bash
$ANDROID_HOME/platform-tools/adb.exe install -r mobile/build/app/outputs/flutter-apk/app-x86_64-release.apk
adb shell am start -n com.georecon.georecon/.MainActivity
```

> El `applicationId` es `com.georecon.georecon`; el nombre del paquete del
> `AndroidManifest.xml` no sirve para lanzar la actividad.

---

## 7. Capturas

### 7.1 Móvil (emulador Android)

```bash
adb exec-out screencap -p > pantalla.png          # 1080×2400
python -c "from PIL import Image; im=Image.open('pantalla.png'); im.thumbnail((540,1200), Image.LANCZOS); im.save('docs/screenshots/result.png')"
```

Trucos que evitan dolores de cabeza:

* En PowerShell, `adb exec-out screencap -p > f.png` **corrompe** el binario; usa
  `cmd /c "adb exec-out screencap -p > f.png"` o redirige desde cmd.
* Para saber dónde tocar sin inspeccionar la UI de Flutter:
  `adb shell uiautomator dump /sdcard/ui.xml` y leer los `bounds`.
* Si el teclado de Android dispara un ANR ("System UI isn't responding"), pulsa
  *Wait* (no *Close app*) y sigue.

### 7.2 CLI

No se captura la terminal: se renderiza. `tools/render_cli_screenshot.py` lanza el
comando real, colorea etiquetas/valores/veredicto y dibuja la ventana con Pillow y
Consolas:

```bash
python tools/render_cli_screenshot.py                 # georecon 8.8.8.8
python tools/render_cli_screenshot.py --cmd "georecon me"
```

Sale en `docs/screenshots/cli.png`.

---

## 8. Integración continua

`.github/workflows/ci.yml`, en cada push a `main` y en cada PR:

* **job `python`** (matrix 3.10 y 3.12): `pip install -e ".[dev]"` → `ruff` →
  `mypy` → `pytest`.
* **job `android`**: Java 17 + Flutter stable con caché → `flutter pub get` →
  `analyze` → `test` → `build apk --release --split-per-abi` → sube los APKs como
  artefacto de la ejecución (`GeoRecon-plus-apk`).

---

## 9. Publicar una versión

```bash
# 1. versiones alineadas: pyproject.toml y mobile/pubspec.yaml (+ CHANGELOG)
# 2. verificar todo
ruff check . && mypy && python -m pytest
cd mobile && flutter analyze && flutter test && flutter build apk --release --split-per-abi

# 3. tag + release
git tag v1.1.0 && git push origin v1.1.0
gh release create v1.1.0 --repo pepehalfonso/geo-recon-plus --title "v1.1.0" \
  --notes-file notas.md --latest

# 4. subir los APK con sus nombres finales
cp mobile/build/app/outputs/flutter-apk/app-arm64-v8a-release.apk      GeoRecon-plus.apk
cp mobile/build/app/outputs/flutter-apk/app-armeabi-v7a-release.apk     GeoRecon-plus-armeabi-v7a.apk
cp mobile/build/app/outputs/flutter-apk/app-x86_64-release.apk          GeoRecon-plus-x86_64.apk
gh release upload v1.1.0 GeoRecon-plus*.apk --repo pepehalfonso/geo-recon-plus --clobber

# 5. repo público
gh repo edit pepehalfonso/geo-recon-plus --visibility public --accept-visibility-change-consequences
```

Notas prácticas:

* La subida a `uploads.github.com` puede ir a 20 KB/s y cortarse con
  `HTTP 408`; los APK de ~8 MB entran, los de 17–48 MB casi nunca. Si hace falta
  subir a mano, `curl.exe -H "Expect:" -H "Authorization: Bearer $(gh auth token)"
  --upload-file … https://uploads.github.com/repos/…/releases/…/assets?name=…`.
* El tag se crea **antes** de tocar más código: si mueves el tag después, quien
  construya desde él obtendrá binarios distintos a los publicados.
* `gh release upload --clobber` reemplaza los assets sin crear duplicados.

---

## 10. Checklist: añadir una blocklist nueva

Ejemplo real de lo que costó meter PSBL:

1. `georecon/providers.py` → añadir la zona a `DNSBL_ZONES`.
2. `mobile/lib/services/api_service.dart` → añadirla a `_dnsblZones`.
3. `mobile/lib/l10n/app_en.arb` y `app_es.arb` → actualizar la línea `sources` del
   pie de pantalla (y ejecutar `flutter gen-l10n`).
4. Tests: si cambia el número esperado de zonas, ajustar `tests/test_providers.py`
   (el resto son afirmaciones sobre notas, no sobre conteos fijos).
5. `CHANGELOG.md` + versión si procede.
6. Verificar todo, reconstruir el APK, reinstalar y comprobar que la pantalla de
   resultado dice `checked 4 DNS blocklists`.
7. Commit + push (el CI lo repite en Linux) y, si hay release, re-subir los APK.

---

## 11. Problemas conocidos y sus soluciones

| Problema | Solución |
| -------- | -------- |
| APK de 48 MB / 17 MB por ABI | `useLegacyPackaging=true` + `--split-per-abi` |
| Subida de assets que corta a los 408 | APK de ~8 MB, o `curl.exe` con cabecera `Expect:` vacía |
| `adb exec-out screencap > archivo` ilegible | redirigir con `cmd /c` |
| Emulador con ANR al abrir el teclado | pulsar *Wait*, o `uiautomator dump` para localizar elementos |
| Falso positivo de DNSBL (`127.255.255.x`) | descartar esa respuesta en lugar de contarla |
| `flutter gen-l10n` ignorando flags de CLI | usa `l10n.yaml`; editar los ARB y re-ejecutar |
| Key de API filtrada en el repo original | aquí la key solo vive en la variable de entorno o en `SharedPreferences` |
