import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../l10n/app_localizations.dart';
import '../models/ip_info.dart';

class ResultScreen extends StatefulWidget {
  const ResultScreen({super.key, required this.result, this.onRefresh});

  final LookupResult result;
  final Future<LookupResult> Function()? onRefresh;

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  late LookupResult _result = widget.result;
  bool _refreshing = false;

  bool get _hasCoordinates =>
      _result.geo.latitude != null && _result.geo.longitude != null;

  Future<void> _refresh() async {
    final reload = widget.onRefresh;
    if (reload == null || _refreshing) return;
    setState(() => _refreshing = true);
    try {
      final fresh = await reload();
      if (!mounted) return;
      setState(() => _result = fresh);
    } finally {
      if (mounted) setState(() => _refreshing = false);
    }
  }

  Future<void> _openMap() async {
    final latitude = _result.geo.latitude;
    final longitude = _result.geo.longitude;
    if (latitude == null || longitude == null) return;
    final uri = Uri.parse(
      'https://www.openstreetmap.org/?mlat=$latitude&mlon=$longitude'
      '#map=12/$latitude/$longitude',
    );
    try {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (_) {
      if (!mounted) return;
      final l10n = AppLocalizations.of(context);
      _snack(l10n.openMapFailed);
    }
  }

  void _snack(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message), duration: const Duration(seconds: 2)));
  }

  Color _verdictColor(BuildContext context) => switch (_result.reputation.verdict) {
        Verdict.clean => const Color(0xFF43A047),
        Verdict.suspicious => const Color(0xFFE0A100),
        Verdict.malicious => const Color(0xFFE53935),
        Verdict.unknown => Theme.of(context).colorScheme.outline,
      };

  String _verdictLabel(AppLocalizations l10n) => switch (_result.reputation.verdict) {
        Verdict.clean => l10n.verdictClean,
        Verdict.suspicious => l10n.verdictSuspicious,
        Verdict.malicious => l10n.verdictMalicious,
        Verdict.unknown => l10n.verdictUnknown,
      };

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;
    final verdictColor = _verdictColor(context);
    final result = _result;

    return Scaffold(
      appBar: AppBar(
        title: result.resolvedFrom == null
            ? Text(result.ip)
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(result.ip, style: Theme.of(context).textTheme.titleLarge),
                  Text(
                    l10n.resolvedFrom(result.resolvedFrom!),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
        actions: [
          if (_hasCoordinates)
            IconButton(
              tooltip: l10n.openMap,
              icon: const Icon(Icons.map_outlined),
              onPressed: _openMap,
            ),
          IconButton(
            tooltip: l10n.copyIp,
            icon: const Icon(Icons.copy),
            onPressed: () => _copy(context, result.ip, l10n.ipCopied),
          ),
          IconButton(
            tooltip: l10n.copyJson,
            icon: const Icon(Icons.data_object),
            onPressed: () => _copy(
              context,
              const JsonEncoder.withIndent('  ').convert(result.toJson()),
              l10n.jsonCopied,
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            if (_refreshing) const LinearProgressIndicator(),
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
                          _verdictLabel(l10n),
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
                      Text(l10n.abuseConfidence(result.reputation.score!)),
                    if (result.reputation.reports != null)
                      Text(l10n.reports(result.reputation.reports!)),
                    if (result.reputation.lastReported != null)
                      Text(l10n.lastReported(result.reputation.lastReported!)),
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
                title: l10n.privateSection,
                rows: [_Row(l10n.scope, _scopeLabel(l10n))],
                trailing: Text(
                  l10n.privateNote,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              )
            else ...[
              _section(
                context,
                icon: Icons.public,
                title: l10n.geoSection,
                rows: [
                  _Row(l10n.country,
                      '${result.geo.flag ?? ''} ${result.geo.country ?? l10n.unknown}'.trim()),
                  _Row(l10n.region, result.geo.region ?? l10n.unknown),
                  _Row(l10n.city, result.geo.city ?? l10n.unknown),
                  _Row(l10n.timezone, result.geo.timezone ?? l10n.unknown),
                  _Row(
                    l10n.coordinates,
                    _hasCoordinates ? result.geo.coordinates : l10n.unknown,
                  ),
                ],
                trailing: _hasCoordinates
                    ? Align(
                        alignment: Alignment.centerLeft,
                        child: TextButton.icon(
                          onPressed: _refreshing ? null : _openMap,
                          icon: const Icon(Icons.map_outlined, size: 18),
                          label: Text(l10n.openMap),
                        ),
                      )
                    : null,
              ),
              _section(
                context,
                icon: Icons.router_outlined,
                title: l10n.networkSection,
                rows: [
                  _Row(l10n.asn, result.connection.asnLabel),
                  _Row(l10n.organization, result.connection.org ?? l10n.unknown),
                  _Row(l10n.isp, result.connection.isp ?? l10n.unknown),
                  _Row(l10n.domain, result.connection.domain ?? l10n.unknown),
                  _Row(l10n.reverseDns, result.hostname ?? l10n.none),
                  _Row(l10n.ipVersion, result.version),
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
              l10n.sourceNote(result.provider),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  String _scopeLabel(AppLocalizations l10n) {
    final ip = _result.ip;
    if (ip.startsWith('127.')) return l10n.scopeLoopback;
    if (ip.startsWith('169.254.')) return l10n.scopeLinkLocal;
    if (ip.startsWith('192.0.2.') || ip.startsWith('198.51.100.') || ip.startsWith('203.0.113.')) {
      return l10n.scopeDocumentation;
    }
    if (ip.startsWith('100.64.')) return l10n.scopeCarrierGrade;
    return l10n.scopePrivate;
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
    _snack(message);
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
