import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../l10n/app_localizations.dart';
import '../services/api_service.dart';
import 'result_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  static const _historyKey = 'history';
  static const _apiKeyPref = 'abuseipdb_key';

  final _controller = TextEditingController();
  final _api = ApiService();

  List<String> _history = <String>[];
  String? _apiKey;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  @override
  void dispose() {
    _controller.dispose();
    _api.dispose();
    super.dispose();
  }

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      _history = (prefs.getStringList(_historyKey) ?? const <String>[]).toList();
      _apiKey = prefs.getString(_apiKeyPref);
    });
  }

  Future<void> _remember(String ip) async {
    final prefs = await SharedPreferences.getInstance();
    _history.remove(ip);
    _history.insert(0, ip);
    if (_history.length > 12) _history = _history.sublist(0, 12);
    await prefs.setStringList(_historyKey, _history);
    if (mounted) setState(() {});
  }

  Future<void> _lookup(String target) async {
    final trimmed = target.trim();
    if (trimmed.isEmpty || _busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await _api.lookup(trimmed, abuseKey: _apiKey);
      await _remember(result.ip);
      if (!mounted) return;
      setState(() => _busy = false);
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ResultScreen(
            result: result,
            onRefresh: () => _api.lookup(trimmed, abuseKey: _apiKey),
          ),
        ),
      );
    } catch (exc) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = exc.toString();
      });
    }
  }

  Future<void> _lookupOwn() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await _api.ownLookup(abuseKey: _apiKey);
      await _remember(result.ip);
      if (!mounted) return;
      setState(() => _busy = false);
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ResultScreen(
            result: result,
            onRefresh: () => _api.ownLookup(abuseKey: _apiKey),
          ),
        ),
      );
    } catch (exc) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = exc.toString();
      });
    }
  }

  Future<void> _openSettings() async {
    final l10n = AppLocalizations.of(context);
    final controller = TextEditingController(text: _apiKey ?? '');
    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.settingsTitle),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.settingsHelp),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              obscureText: true,
              decoration: InputDecoration(
                labelText: l10n.apiKeyLabel,
                hintText: l10n.apiKeyHint,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.save),
          ),
        ],
      ),
    );
    if (saved == true) {
      final prefs = await SharedPreferences.getInstance();
      final value = controller.text.trim();
      if (value.isEmpty) {
        await prefs.remove(_apiKeyPref);
      } else {
        await prefs.setString(_apiKeyPref, value);
      }
      if (mounted) setState(() => _apiKey = value.isEmpty ? null : value);
    }
    controller.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('GeoRecon+'),
        actions: [
          IconButton(
            onPressed: _openSettings,
            icon: const Icon(Icons.key),
            tooltip: l10n.settingsTitle,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadPreferences,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              l10n.tagline,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 4),
            Text(
              _apiKey == null ? l10n.statusNoKey : l10n.statusHasKey,
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _controller,
              keyboardType: TextInputType.url,
              textInputAction: TextInputAction.search,
              onSubmitted: _lookup,
              decoration: InputDecoration(
                labelText: l10n.inputLabel,
                hintText: l10n.inputHint,
                prefixIcon: const Icon(Icons.dns_outlined),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _busy ? null : () => _lookup(_controller.text),
                    icon: const Icon(Icons.search),
                    label: Text(l10n.lookUp),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _busy ? null : _lookupOwn,
                    icon: const Icon(Icons.my_location),
                    label: Text(l10n.myIp),
                  ),
                ),
              ],
            ),
            if (_busy) const Padding(
              padding: EdgeInsets.only(top: 16),
              child: LinearProgressIndicator(),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 16),
                child: Card(
                  color: Theme.of(context).colorScheme.errorContainer,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        Icon(Icons.error_outline,
                            color: Theme.of(context).colorScheme.onErrorContainer),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            _error!,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.onErrorContainer,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            if (_history.isNotEmpty) ...[
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(l10n.recent, style: Theme.of(context).textTheme.titleMedium),
                  TextButton(
                    onPressed: () async {
                      final prefs = await SharedPreferences.getInstance();
                      await prefs.remove(_historyKey);
                      if (mounted) setState(() => _history = <String>[]);
                    },
                    child: Text(l10n.clear),
                  ),
                ],
              ),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final ip in _history)
                    ActionChip(
                      label: Text(ip),
                      avatar: const Icon(Icons.history, size: 18),
                      onPressed: () {
                        _controller.text = ip;
                        _lookup(ip);
                      },
                    ),
                ],
              ),
            ],
            const SizedBox(height: 32),
            Text(
              l10n.sources,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}
