// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get tagline => 'IP geolocation & reputation';

  @override
  String get statusNoKey =>
      'Reputation via free DNS blocklists. Add an AbuseIPDB key for full reports.';

  @override
  String get statusHasKey =>
      'AbuseIPDB key active: full reputation reports enabled.';

  @override
  String get inputLabel => 'IP address or domain';

  @override
  String get inputHint => '8.8.8.8';

  @override
  String get lookUp => 'Look up';

  @override
  String get myIp => 'My IP';

  @override
  String get recent => 'Recent';

  @override
  String get clear => 'Clear';

  @override
  String get refresh => 'Refresh';

  @override
  String get sources =>
      'Data: ipwho.is, ipify, Google DNS, Spamhaus / SpamCop / Barracudacentral.';

  @override
  String get settingsTitle => 'AbuseIPDB API key';

  @override
  String get settingsHelp =>
      'Optional. Without it the app uses free DNS blocklists only. Get one at abuseipdb.com.';

  @override
  String get apiKeyLabel => 'API key';

  @override
  String get apiKeyHint => 'paste your key';

  @override
  String get cancel => 'Cancel';

  @override
  String get save => 'Save';

  @override
  String get copyIp => 'Copy IP';

  @override
  String get copyJson => 'Copy report as JSON';

  @override
  String get ipCopied => 'IP copied';

  @override
  String get jsonCopied => 'JSON report copied';

  @override
  String get verdictClean => 'CLEAN';

  @override
  String get verdictSuspicious => 'SUSPICIOUS';

  @override
  String get verdictMalicious => 'MALICIOUS';

  @override
  String get verdictUnknown => 'UNKNOWN';

  @override
  String abuseConfidence(Object score) {
    return 'Abuse confidence: $score/100';
  }

  @override
  String reports(Object count) {
    return 'Reports: $count';
  }

  @override
  String lastReported(Object date) {
    return 'Last reported: $date';
  }

  @override
  String get privateSection => 'Non-public address';

  @override
  String get scope => 'Scope';

  @override
  String get privateNote =>
      'There is no public geolocation data for this address.';

  @override
  String get geoSection => 'Geolocation';

  @override
  String get country => 'Country';

  @override
  String get region => 'Region';

  @override
  String get city => 'City';

  @override
  String get timezone => 'Timezone';

  @override
  String get coordinates => 'Coordinates';

  @override
  String get networkSection => 'Network';

  @override
  String get asn => 'ASN';

  @override
  String get organization => 'Organization';

  @override
  String get isp => 'ISP';

  @override
  String get domain => 'Domain';

  @override
  String get reverseDns => 'Reverse DNS';

  @override
  String get ipVersion => 'Version';

  @override
  String get unknown => 'unknown';

  @override
  String get none => 'none';

  @override
  String sourceNote(Object provider) {
    return 'Source: $provider · geolocation is an estimate, not a physical trace.';
  }

  @override
  String get openMap => 'Open on map';

  @override
  String get openMapFailed => 'Could not open the map.';

  @override
  String resolvedFrom(Object host) {
    return 'Resolved from $host';
  }

  @override
  String get scopeLoopback => 'loopback';

  @override
  String get scopeLinkLocal => 'link-local';

  @override
  String get scopeDocumentation => 'documentation';

  @override
  String get scopeCarrierGrade => 'carrier-grade NAT';

  @override
  String get scopePrivate => 'private';
}
