// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get tagline => 'Geolocalización y reputación de IP';

  @override
  String get statusNoKey =>
      'Reputación mediante listas DNS gratuitas. Añade una clave de AbuseIPDB para informes completos.';

  @override
  String get statusHasKey =>
      'Clave de AbuseIPDB activa: informes de reputación completos.';

  @override
  String get inputLabel => 'Dirección IP o dominio';

  @override
  String get inputHint => '8.8.8.8';

  @override
  String get lookUp => 'Consultar';

  @override
  String get myIp => 'Mi IP';

  @override
  String get recent => 'Recientes';

  @override
  String get clear => 'Borrar';

  @override
  String get refresh => 'Actualizar';

  @override
  String get sources =>
      'Datos: ipwho.is, ipify, Google DNS, Spamhaus / SpamCop / PSBL / Barracudacentral.';

  @override
  String get settingsTitle => 'Clave de AbuseIPDB';

  @override
  String get settingsHelp =>
      'Opcional. Sin ella solo se usan listas DNS gratuitas. Consíguela en abuseipdb.com.';

  @override
  String get apiKeyLabel => 'Clave API';

  @override
  String get apiKeyHint => 'pega tu clave';

  @override
  String get cancel => 'Cancelar';

  @override
  String get save => 'Guardar';

  @override
  String get copyIp => 'Copiar IP';

  @override
  String get copyJson => 'Copiar informe en JSON';

  @override
  String get ipCopied => 'IP copiada';

  @override
  String get jsonCopied => 'Informe JSON copiado';

  @override
  String get verdictClean => 'LIMPIO';

  @override
  String get verdictSuspicious => 'SOSPECHOSO';

  @override
  String get verdictMalicious => 'MALICIOSO';

  @override
  String get verdictUnknown => 'DESCONOCIDO';

  @override
  String abuseConfidence(Object score) {
    return 'Confianza de abuso: $score/100';
  }

  @override
  String reports(Object count) {
    return 'Denuncias: $count';
  }

  @override
  String lastReported(Object date) {
    return 'Última denuncia: $date';
  }

  @override
  String get privateSection => 'Dirección no pública';

  @override
  String get scope => 'Alcance';

  @override
  String get privateNote =>
      'No hay datos públicos de geolocalización para esta dirección.';

  @override
  String get geoSection => 'Geolocalización';

  @override
  String get country => 'País';

  @override
  String get region => 'Región';

  @override
  String get city => 'Ciudad';

  @override
  String get timezone => 'Zona horaria';

  @override
  String get coordinates => 'Coordenadas';

  @override
  String get networkSection => 'Red';

  @override
  String get asn => 'ASN';

  @override
  String get organization => 'Organización';

  @override
  String get isp => 'ISP';

  @override
  String get domain => 'Dominio';

  @override
  String get reverseDns => 'DNS inverso';

  @override
  String get ipVersion => 'Versión';

  @override
  String get unknown => 'desconocido';

  @override
  String get none => 'ninguno';

  @override
  String sourceNote(Object provider) {
    return 'Fuente: $provider · la geolocalización es una estimación, no un rastreo físico.';
  }

  @override
  String get openMap => 'Abrir en el mapa';

  @override
  String get openMapFailed => 'No se pudo abrir el mapa.';

  @override
  String resolvedFrom(Object host) {
    return 'Resuelto desde $host';
  }

  @override
  String get scopeLoopback => 'loopback';

  @override
  String get scopeLinkLocal => 'enlace local';

  @override
  String get scopeDocumentation => 'documentación';

  @override
  String get scopeCarrierGrade => 'NAT de operador';

  @override
  String get scopePrivate => 'privada';
}
