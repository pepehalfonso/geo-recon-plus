import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

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
        MaterialPageRoute<void>(builder: (_) => ResultScreen(result: result)),
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
        MaterialPageRoute<void>(builder: (_) => ResultScreen(result: result)),
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
    final controller = TextEditingController(text: _apiKey ?? '');
    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('AbuseIPDB API key'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Optional. Without it the app uses free DNS blocklists only. '
              'Get one at abuseipdb.com.',
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'API key',
                hintText: 'paste your key',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Save'),
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
    return Scaffold(
      appBar: AppBar(
        title: const Text('GeoRecon+'),
        actions: [
          IconButton(
            onPressed: _openSettings,
            icon: const Icon(Icons.key),
            tooltip: 'AbuseIPDB API key',
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'IP geolocation & reputation',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 4),
          Text(
            _apiKey == null
                ? 'Reputation via free DNS blocklists. Add an AbuseIPDB key for full reports.'
                : 'AbuseIPDB key active: full reputation reports enabled.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _controller,
            keyboardType: TextInputType.url,
            textInputAction: TextInputAction.search,
            onSubmitted: _lookup,
            decoration: const InputDecoration(
              labelText: 'IP address',
              hintText: '8.8.8.8',
              prefixIcon: Icon(Icons.dns_outlined),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: _busy ? null : () => _lookup(_controller.text),
                  icon: const Icon(Icons.search),
                  label: const Text('Look up'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _busy ? null : _lookupOwn,
                  icon: const Icon(Icons.my_location),
                  label: const Text('My IP'),
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
                Text('Recent', style: Theme.of(context).textTheme.titleMedium),
                TextButton(
                  onPressed: () async {
                    final prefs = await SharedPreferences.getInstance();
                    await prefs.remove(_historyKey);
                    if (mounted) setState(() => _history = <String>[]);
                  },
                  child: const Text('Clear'),
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
            'Data: ipwho.is, ipify, Google DNS, Spamhaus / SpamCop / Barracudacentral.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
