import 'package:flutter_test/flutter_test.dart';
import 'package:door_motor/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(DoorMotorApp());
  });
}