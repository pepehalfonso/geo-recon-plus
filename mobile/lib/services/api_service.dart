import 'dart:async';
import 'dart:convert';
import 'dart:io';

import '../models/ip_info.dart';

class LookupException implements Exception {
  const LookupException(this.message);

  final String message;

  @override
  String toString() => message;
}

class ApiService {
  ApiService({HttpClient? client}) : _client = client ?? HttpClient() {
    _client.connectionTimeout = const Duration(seconds: 12);
  }

  static const _dnsblZones = [
    'zen.spamhaus.org',
    'bl.spamcop.net',
    'b.barracudacentral.org',
  ];

  static const _specialV4Networks = [
    ('192.0.2.0', 24),
    ('198.51.100.0', 24),
    ('203.0.113.0', 24),
    ('198.18.0.0', 15),
    ('100.64.0.0', 10),
    ('10.0.0.0', 8),
    ('172.16.0.0', 12),
    ('192.168.0.0', 16),
    ('169.254.0.0', 16),
    ('127.0.0.0', 8),
  ];

  final HttpClient _client;

  void dispose() => _client.close(force: true);

  Future<LookupResult> lookup(String target, {String? abuseKey}) async {
    final address = InternetAddress.tryParse(target.trim());
    if (address == null) {
      throw const LookupException('Not a valid IP address');
    }

    final scope = scopeOf(address);
    if (scope != null) {
      final result = LookupResult(ip: address.address, isPrivate: true);
      result.reputation.notes.add('${address.address} is a $scope address, so there is no public data for it');
      return result;
    }

    final geo = await _geoLookup(address.address);
    final hostname = await reverseDns(address.address);
    final warnings = <String>[];
    final rep = await reputation(address.address, abuseKey: abuseKey, warnings: warnings);
    return LookupResult(
      ip: address.address,
      version: address.type == InternetAddressType.IPv4 ? 'IPv4' : 'IPv6',
      geo: geo.geo,
      connection: geo.connection,
      reputation: rep,
      hostname: hostname,
      provider: 'ipwho.is',
      warnings: warnings,
    );
  }

  Future<LookupResult> ownLookup({String? abuseKey}) async {
    String ip;
    try {
      final self = await _getJson(Uri.parse('https://ipwho.is/'));
      if (self is! Map<String, dynamic> || self['success'] == false || self['ip'] == null) {
        throw const LookupException('ipwho.is did not return an IP');
      }
      ip = self['ip'] as String;
    } catch (_) {
      final fallback = await _getJson(Uri.parse('https://api.ipify.org?format=json'));
      ip = (fallback as Map<String, dynamic>)['ip'] as String;
    }
    return lookup(ip, abuseKey: abuseKey);
  }

  Future<String?> reverseDns(String ip) async {
    final name = _ptrName(ip);
    if (name == null) return null;
    try {
      final body = await _getJson(Uri.parse('https://dns.google/resolve?name=$name&type=PTR'));
      if (body is! Map<String, dynamic> || body['Status'] != 0) return null;
      final answers = body['Answer'] as List<dynamic>? ?? const [];
      for (final answer in answers) {
        final data = (answer as Map<String, dynamic>)['data'] as String?;
        if (data != null && data.isNotEmpty) return data.replaceAll(RegExp(r'\.$'), '');
      }
      return null;
    } on LookupException {
      return null;
    } on SocketException {
      return null;
    }
  }

  Future<Reputation> reputation(
    String ip, {
    String? abuseKey,
    List<String>? warnings,
  }) async {
    final collected = warnings ?? <String>[];
    Reputation primary = Reputation();
    if (abuseKey != null && abuseKey.isNotEmpty) {
      try {
        primary = await _abuseIpDb(ip, abuseKey);
      } on LookupException catch (exc) {
        collected.add('AbuseIPDB skipped: ${exc.message}');
      } on SocketException {
        collected.add('AbuseIPDB skipped: network unreachable');
      } on TimeoutException {
        collected.add('AbuseIPDB skipped: request timed out');
      }
    }

    final secondary = await dnsbl(ip);
    return mergeReputation(primary, secondary);
  }

  Future<Reputation> dnsbl(String ip) async {
    if (ip.contains(':')) {
      return Reputation(source: 'dnsbl', notes: const ['DNSBL lists are IPv4-only']);
    }
    final octets = ip.split('.');
    if (octets.length != 4) return Reputation(source: 'dnsbl');
    final reversedIp = octets.reversed.join('.');

    final listed = <String>[];
    var checked = 0;
    for (final zone in _dnsblZones) {
      try {
        final body = await _getJson(
          Uri.parse('https://dns.google/resolve?name=$reversedIp.$zone&type=A'),
        );
      if (body is! Map<String, dynamic>) continue;
      final status = body['Status'];
      if (status != 0 && status != 3) continue;
      checked++;
      if (status != 0) continue;
      final answers = body['Answer'] as List<dynamic>? ?? const [];
        for (final answer in answers) {
          final data = (answer as Map<String, dynamic>)['data'] as String? ?? '';
          if (data.startsWith('127.')) {
            listed.add('$zone ($data)');
            break;
          }
        }
      } on LookupException {
        continue;
      } on SocketException {
        continue;
      }
    }

    if (checked == 0) {
      return Reputation(source: 'dnsbl', notes: const ['no blocklist reachable']);
    }
    final reputation = Reputation(source: 'dnsbl')
      ..notes.add('checked $checked DNS blocklists');
    if (listed.isEmpty) {
      reputation.verdict = Verdict.clean;
      reputation.notes.add('not listed on any checked blocklist');
    } else {
      reputation.verdict = Verdict.suspicious;
      reputation.notes.addAll(listed.map((entry) => 'listed on $entry'));
    }
    return reputation;
  }

  Future<Reputation> _abuseIpDb(String ip, String key) async {
    final uri = Uri.parse('https://api.abuseipdb.com/api/v2/check?ipAddress=$ip&maxAgeInDays=90');
    final body = await _getJson(uri, headers: {'Key': key, 'Accept': 'application/json'});
    if (body is! Map<String, dynamic>) {
      throw const LookupException('AbuseIPDB returned an unexpected payload');
    }
    if (body['errors'] is List && (body['errors'] as List).isNotEmpty) {
      final details = (body['errors'] as List)
          .map((error) => '${(error as Map<String, dynamic>)['detail']}')
          .join('; ');
      throw LookupException('AbuseIPDB: $details');
    }
    final data = body['data'] as Map<String, dynamic>? ?? const {};
    final score = (data['abuseConfidenceScore'] as num?)?.toInt();
    return Reputation(
      source: 'abuseipdb',
      score: score,
      reports: (data['totalReports'] as num?)?.toInt(),
      lastReported: data['lastReportedAt'] as String?,
      whitelisted: data['isWhitelisted'] as bool?,
      verdict: verdictFromScore(score),
      notes: [
        'usage type: ${data['usageType'] ?? 'unknown'}',
        if (data['domain'] != null) 'domain: ${data['domain']}',
      ],
    );
  }

  Future<({GeoInfo geo, ConnectionInfo connection})> _geoLookup(String ip) async {
    final body = await _getJson(Uri.parse('https://ipwho.is/$ip'));
    if (body is! Map<String, dynamic>) {
      throw const LookupException('ipwho.is returned an unexpected payload');
    }
    if (body['success'] == false) {
      throw LookupException('ipwho.is: ${body['message'] ?? 'lookup refused'}');
    }
    final connection = body['connection'] is Map<String, dynamic>
        ? ConnectionInfo.fromJson(body['connection'] as Map<String, dynamic>)
        : const ConnectionInfo();
    return (geo: GeoInfo.fromJson(body), connection: connection);
  }

  Future<dynamic> _getJson(Uri uri, {Map<String, String>? headers}) async {
    final request = await _client.getUrl(uri).timeout(const Duration(seconds: 12));
    request.headers.set(HttpHeaders.acceptHeader, 'application/json');
    request.headers.set(HttpHeaders.userAgentHeader, 'georecon-plus-mobile/1.0');
    headers?.forEach(request.headers.set);

    final response = await request.close().timeout(const Duration(seconds: 15));
    final raw = await response.transform(utf8.decoder).join();
    if (response.statusCode >= 500) {
      throw LookupException('${uri.host} answered HTTP ${response.statusCode}');
    }
    try {
      return jsonDecode(raw);
    } on FormatException {
      throw LookupException('${uri.host} did not return JSON');
    }
  }

  static String? scopeOf(InternetAddress address) {
    if (address.isLoopback) return 'loopback';
    if (address.isLinkLocal) return 'link-local';
    if (address.isMulticast) return 'multicast';
    if (address.type == InternetAddressType.IPv4) {
      for (final (base, bits) in _specialV4Networks) {
        if (_inCidr(address, base, bits)) return _labelFor(base, bits);
      }
    }
    return null;
  }

  static Verdict verdictFromScore(int? score) {
    if (score == null) return Verdict.unknown;
    if (score >= 75) return Verdict.malicious;
    if (score >= 25) return Verdict.suspicious;
    return Verdict.clean;
  }

  static Reputation mergeReputation(Reputation primary, Reputation secondary) {
    if (primary.source == 'none') return secondary;
    primary.notes.addAll(secondary.notes);
    if (secondary.verdict == Verdict.suspicious && primary.verdict == Verdict.clean) {
      primary.verdict = Verdict.suspicious;
      primary.notes.add('upgraded: listed on a DNS blocklist');
    }
    return primary;
  }

  static String _labelFor(String base, int bits) {
    if (base == '100.64.0.0') return 'carrier-grade NAT';
    if (base == '192.0.2.0' || base == '198.51.100.0' || base == '203.0.113.0') return 'documentation';
    if (base == '198.18.0.0') return 'benchmarking';
    if (base == '127.0.0.0') return 'loopback';
    if (base == '169.254.0.0') return 'link-local';
    return 'private';
  }

  static bool _inCidr(InternetAddress address, String base, int bits) {
    final target = InternetAddress.tryParse(base);
    if (target == null || target.type != address.type) return false;
    final size = bits == 0 ? 0 : (1 << (32 - bits));
    final start = _toInt(target);
    final value = _toInt(address);
    return value >= start && value < start + size;
  }

  static int _toInt(InternetAddress address) {
    final octets = address.rawAddress;
    var value = 0;
    for (final octet in octets) {
      value = (value << 8) | octet;
    }
    return value;
  }

  static String? _ptrName(String ip) {
    final address = InternetAddress.tryParse(ip);
    if (address == null) return null;
    if (address.type == InternetAddressType.IPv4) {
      return '${address.rawAddress.reversed.join('.')}.in-addr.arpa';
    }
    final nibbles = address.rawAddress.reversed.map((b) => b.toRadixString(16)).join('.');
    return '$nibbles.ip6.arpa';
  }
}
