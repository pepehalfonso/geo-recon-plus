import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/ip_info.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key, required this.result});

  final LookupResult result;

  Color _verdictColor(BuildContext context) => switch (result.reputation.verdict) {
        Verdict.clean => const Color(0xFF43A047),
        Verdict.suspicious => const Color(0xFFE0A100),
        Verdict.malicious => const Color(0xFFE53935),
        Verdict.unknown => Theme.of(context).colorScheme.outline,
      };

  String get _verdictLabel => switch (result.reputation.verdict) {
        Verdict.clean => 'CLEAN',
        Verdict.suspicious => 'SUSPICIOUS',
        Verdict.malicious => 'MALICIOUS',
        Verdict.unknown => 'UNKNOWN',
      };

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final verdictColor = _verdictColor(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(result.ip),
        actions: [
          IconButton(
            tooltip: 'Copy IP',
            icon: const Icon(Icons.copy),
            onPressed: () => _copy(context, result.ip, 'IP copied'),
          ),
          IconButton(
            tooltip: 'Copy report as JSON',
            icon: const Icon(Icons.data_object),
            onPressed: () => _copy(
              context,
              const JsonEncoder.withIndent('  ').convert(result.toJson()),
              'JSON report copied',
            ),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            color: verdictColor.withValues(alpha: 0.16),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.verified_user_outlined, color: verdictColor),
                      const SizedBox(width: 8),
                      Text(
                        _verdictLabel,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              color: verdictColor,
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      const Spacer(),
                      Chip(
                        label: Text(result.reputation.source),
                        visualDensity: VisualDensity.compact,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (result.reputation.score != null)
                    Text('Abuse confidence: ${result.reputation.score}/100'),
                  if (result.reputation.reports != null)
                    Text('Reports: ${result.reputation.reports}'),
                  if (result.reputation.lastReported != null)
                    Text('Last reported: ${result.reputation.lastReported}'),
                  for (final note in result.reputation.notes)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text('• $note', style: Theme.of(context).textTheme.bodySmall),
                    ),
                ],
              ),
            ),
          ),
          if (result.isPrivate)
            _section(
              context,
              icon: Icons.lock_outline,
              title: 'Non-public address',
              rows: [
                _Row('Scope', _scopeLabel()),
              ],
              trailing: Text(
                'There is no public geolocation data for this address.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            )
          else ...[
            _section(
              context,
              icon: Icons.public,
              title: 'Geolocation',
              rows: [
                _Row('Country', '${result.geo.flag ?? ''} ${result.geo.country ?? 'unknown'}'.trim()),
                _Row('Region', result.geo.region ?? 'unknown'),
                _Row('City', result.geo.city ?? 'unknown'),
                _Row('Timezone', result.geo.timezone ?? 'unknown'),
                _Row('Coordinates', result.geo.coordinates),
              ],
            ),
            _section(
              context,
              icon: Icons.router_outlined,
              title: 'Network',
              rows: [
                _Row('ASN', result.connection.asnLabel),
                _Row('Organization', result.connection.org ?? 'unknown'),
                _Row('ISP', result.connection.isp ?? 'unknown'),
                _Row('Domain', result.connection.domain ?? 'unknown'),
                _Row('Reverse DNS', result.hostname ?? 'none'),
                _Row('Version', result.version),
              ],
            ),
          ],
          if (result.warnings.isNotEmpty)
            Card(
              color: scheme.tertiaryContainer,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    for (final warning in result.warnings)
                      Text(
                        '! $warning',
                        style: TextStyle(color: scheme.onTertiaryContainer),
                      ),
                  ],
                ),
              ),
            ),
          const SizedBox(height: 12),
          Text(
            'Source: ${result.provider} · geolocation is an estimate, not a physical trace.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }

  String _scopeLabel() {
    final ip = result.ip;
    if (ip.startsWith('127.')) return 'loopback';
    if (ip.startsWith('169.254.')) return 'link-local';
    if (ip.startsWith('192.0.2.') || ip.startsWith('198.51.100.') || ip.startsWith('203.0.113.')) {
      return 'documentation';
    }
    if (ip.startsWith('100.64.')) return 'carrier-grade NAT';
    return 'private';
  }

  Widget _section(
    BuildContext context, {
    required IconData icon,
    required String title,
    required List<_Row> rows,
    Widget? trailing,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, size: 20),
                const SizedBox(width: 8),
                Text(title, style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const SizedBox(height: 12),
            for (final row in rows) row.build(context),
            if (trailing != null) ...[const SizedBox(height: 8), trailing],
          ],
        ),
      ),
    );
  }

  Future<void> _copy(BuildContext context, String text, String message) async {
    await Clipboard.setData(ClipboardData(text: text));
    if (!context.mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message), duration: const Duration(seconds: 2)));
  }
}

class _Row {
  const _Row(this.label, this.value);

  final String label;
  final String value;

  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Theme.of(context).colorScheme.outline),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
