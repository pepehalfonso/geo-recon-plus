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
}
