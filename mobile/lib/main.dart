import 'package:flutter/material.dart';

import 'l10n/app_localizations.dart';
import 'screens/home_screen.dart';

void main() => runApp(const GeoReconApp());

class GeoReconApp extends StatelessWidget {
  const GeoReconApp({super.key, this.locale});

  /// Test hook: lets the widget tests pin a locale instead of the system one.
  final Locale? locale;

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF00B3A4),
      brightness: Brightness.dark,
    );

    return MaterialApp(
      title: 'GeoRecon+',
      debugShowCheckedModeBanner: false,
      locale: locale,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: scheme,
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
        ),
        cardTheme: const CardThemeData(
          clipBehavior: Clip.antiAlias,
          margin: EdgeInsets.only(bottom: 12),
        ),
      ),
      home: const HomeScreen(),
    );
  }
}
