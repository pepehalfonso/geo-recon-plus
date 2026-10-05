enum Verdict { clean, suspicious, malicious, unknown }

class GeoInfo {
  const GeoInfo({
    this.country,
    this.countryCode,
    this.region,
    this.city,
    this.latitude,
    this.longitude,
    this.timezone,
    this.postal,
    this.flag,
  });

  final String? country;
  final String? countryCode;
  final String? region;
  final String? city;
  final double? latitude;
  final double? longitude;
  final String? timezone;
  final String? postal;
  final String? flag;

  String get place {
    final parts = <String>[?city, ?region, ?country];
    return parts.isEmpty ? 'unknown' : parts.join(', ');
  }

  String get coordinates => (latitude == null || longitude == null)
      ? 'unknown'
      : '${latitude!.toStringAsFixed(4)}, ${longitude!.toStringAsFixed(4)}';

  factory GeoInfo.fromJson(Map<String, dynamic> json) {
    final timezone = json['timezone'];
    return GeoInfo(
      country: json['country'] as String?,
      countryCode: json['country_code'] as String?,
      region: json['region'] as String?,
      city: json['city'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      timezone: timezone is Map<String, dynamic> ? timezone['id'] as String? : null,
      postal: json['postal'] as String?,
      flag: _flag(json['country_code'] as String?),
    );
  }

  static String? _flag(String? code) {
    if (code == null || code.length != 2) return null;
    final base = 0x1F1E6 - 'A'.codeUnitAt(0);
    return String.fromCharCodes([
      base + code.toUpperCase().codeUnitAt(0),
      base + code.toUpperCase().codeUnitAt(1),
    ]);
  }
}

class ConnectionInfo {
  const ConnectionInfo({this.asn, this.org, this.isp, this.domain});

  final int? asn;
  final String? org;
  final String? isp;
  final String? domain;

  String get asnLabel => asn == null ? 'unknown' : 'AS$asn';

  factory ConnectionInfo.fromJson(Map<String, dynamic> json) => ConnectionInfo(
        asn: (json['asn'] as num?)?.toInt(),
        org: json['org'] as String?,
        isp: json['isp'] as String?,
        domain: json['domain'] as String?,
      );
}

class Reputation {
  Reputation({
    this.source = 'none',
    this.score,
    this.reports,
    this.lastReported,
    this.whitelisted,
    this.verdict = Verdict.unknown,
    List<String>? notes,
  }) : notes = notes ?? <String>[];

  final String source;
  final int? score;
  final int? reports;
  final String? lastReported;
  final bool? whitelisted;
  Verdict verdict;
  final List<String> notes;
}

class LookupResult {
  LookupResult({
    required this.ip,
    this.version = 'IPv4',
    GeoInfo? geo,
    ConnectionInfo? connection,
    Reputation? reputation,
    this.isPrivate = false,
    this.hostname,
    this.resolvedFrom,
    this.provider = 'ipwho.is',
    List<String>? warnings,
  })  : geo = geo ?? GeoInfo(),
        connection = connection ?? ConnectionInfo(),
        reputation = reputation ?? Reputation(),
        warnings = warnings ?? <String>[];

  final String ip;
  final String version;
  final GeoInfo geo;
  final ConnectionInfo connection;
  final Reputation reputation;
  final bool isPrivate;
  final String? hostname;
  final String? resolvedFrom;
  final String provider;
  final List<String> warnings;

  Map<String, dynamic> toJson() => {
        'ip': ip,
        'version': version,
        'geo': {
          'country': geo.country,
          'country_code': geo.countryCode,
          'region': geo.region,
          'city': geo.city,
          'latitude': geo.latitude,
          'longitude': geo.longitude,
          'timezone': geo.timezone,
          'postal': geo.postal,
        },
        'connection': {
          'asn': connection.asn,
          'org': connection.org,
          'isp': connection.isp,
          'domain': connection.domain,
        },
        'reputation': {
          'source': reputation.source,
          'score': reputation.score,
          'reports': reputation.reports,
          'last_reported': reputation.lastReported,
          'whitelisted': reputation.whitelisted,
          'verdict': reputation.verdict.name,
          'notes': reputation.notes,
        },
        'is_private': isPrivate,
        'hostname': hostname,
        'resolved_from': resolvedFrom,
        'provider': provider,
        'warnings': warnings,
      };
}

Verdict verdictFromName(String? name) => switch (name) {
      'clean' => Verdict.clean,
      'suspicious' => Verdict.suspicious,
      'malicious' => Verdict.malicious,
      _ => Verdict.unknown,
    };
