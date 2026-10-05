import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:georecon/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('home screen renders the lookup form', (tester) async {
    SharedPreferences.setMockInitialValues({});

    await tester.pumpWidget(const GeoReconApp());
    await tester.pump();

    expect(find.text('GeoRecon+'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.text('Look up'), findsOneWidget);
    expect(find.text('My IP'), findsOneWidget);
  });

  testWidgets('home screen follows the device language', (tester) async {
    SharedPreferences.setMockInitialValues({});

    await tester.pumpWidget(const GeoReconApp(locale: Locale('es')));
    await tester.pump();

    expect(find.text('Consultar'), findsOneWidget);
    expect(find.text('Mi IP'), findsOneWidget);
    expect(find.text('IP geolocation & reputation'), findsNothing);
    expect(find.text('Geolocalización y reputación de IP'), findsOneWidget);
  });
}
