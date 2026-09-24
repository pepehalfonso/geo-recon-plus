# GeoRecon+ (Android)

App móvil de [GeoRecon+](../README.md): geolocalización y reputación de IPs.

## Compilar el APK

```bash
flutter pub get
flutter build apk --release
# mobile/build/app/outputs/flutter-apk/app-release.apk
```

Requiere Flutter 3.x con el toolchain de Android configurado (`flutter doctor`).

## Tests

```bash
flutter analyze   # sin issues
flutter test      # 1 widget test + 5 tests de red en vivo
```

## Funciones

* Lookup de cualquier IP pública y detección de la IP propia.
* IP privadas / de documentación: aviso inmediato, sin llamadas de red.
* Reputación por DNS blocklists sin key; con key de AbuseIPDB informe completo.
* Historial persistente y configuración de la key desde la app.
* Copiar IP o informe JSON al portapapeles.

Las fuentes de datos son las mismas que la CLI: `ipwho.is`, `ipify`, DNS-over-HTTPS y,
opcionalmente, AbuseIPDB.
