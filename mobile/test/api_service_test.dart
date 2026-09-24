import 'package:flutter_test/flutter_test.dart';
import 'package:georecon/models/ip_info.dart';
import 'package:georecon/services/api_service.dart';

void main() {
  late ApiService api;

  setUp(() => api = ApiService());
  tearDown(() => api.dispose());

  test('resolves a public IP to geo, network and reverse DNS', () async {
    final result = await api.lookup('8.8.8.8');

    expect(result.isPrivate, isFalse);
    expect(result.geo.country, 'United States');
    expect(result.connection.asn, 15169);
    expect(result.connection.isp, 'Google LLC');
    expect(result.hostname, 'dns.google');
    expect(result.reputation.source, 'dnsbl');
    expect(result.reputation.verdict, Verdict.clean);
  }, timeout: const Timeout(Duration(seconds: 60)));

  test('detects the public IP of the device', () async {
    final result = await api.ownLookup();

    expect(result.ip, isNotEmpty);
    expect(result.isPrivate, isFalse);
    expect(result.geo.country, isNotNull);
  }, timeout: const Timeout(Duration(seconds: 60)));

  test('refuses malformed input without touching the network', () async {
    await expectLater(
      api.lookup('nope'),
      throwsA(isA<LookupException>().having((e) => e.message, 'message', contains('valid IP'))),
    );
  });

  test('skips geolocation for private addresses', () async {
    final result = await api.lookup('192.168.1.4');

    expect(result.isPrivate, isTrue);
    expect(result.geo.country, isNull);
    expect(result.reputation.verdict, Verdict.unknown);
    expect(result.reputation.notes.single, contains('private'));
  });

  test('reports unreachable AbuseIPDB as a warning, not a crash', () async {
    final result = await api.lookup('1.1.1.1', abuseKey: 'not-a-real-key');

    expect(result.geo.country, isNotNull);
    expect(result.reputation.verdict, Verdict.clean);
    expect(result.warnings, isNotEmpty);
    expect(
      result.warnings.any((warning) => warning.contains('AbuseIPDB')),
      isTrue,
    );
  }, timeout: const Timeout(Duration(seconds: 60)));
}
