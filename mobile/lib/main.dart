import 'package:flutter/material.dart';

import 'screens/home_screen.dart';

void main() => runApp(const GeoReconApp());

class GeoReconApp extends StatelessWidget {
  const GeoReconApp({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF00B3A4),
      brightness: Brightness.dark,
    );

    return MaterialApp(
      title: 'GeoRecon+',
      debugShowCheckedModeBanner: false,
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
