import 'package:flutter/material.dart';
import 'package:door_motor/screens/home_screen.dart';
import 'package:door_motor/screens/schedule_screen.dart';
import 'package:door_motor/ble/ble_manager.dart';

void main() {
  runApp(DoorMotorApp());
}

class DoorMotorApp extends StatelessWidget {
  DoorMotorApp({super.key});

  final BleManager _ble = BleManager();

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DoorMotor',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => HomeScreen(ble: _ble),
        '/schedule': (context) => ScheduleScreen(ble: _ble),
      },
    );
  }
}