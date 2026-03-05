import 'package:flutter/material.dart';
import 'package:door_motor/screens/home_screen.dart';
import 'package:door_motor/screens/schedule_screen.dart';
import 'package:door_motor/screens/settings_screen.dart';
import 'package:door_motor/screens/stats_screen.dart';
import 'package:door_motor/ble/ble_manager.dart';
import 'package:door_motor/services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService().initialize();
  runApp(DoorMotorApp());
}

class DoorMotorApp extends StatefulWidget {
  DoorMotorApp({super.key});

  @override
  State<DoorMotorApp> createState() => _DoorMotorAppState();
}

class _DoorMotorAppState extends State<DoorMotorApp> {
  final BleManager _ble = BleManager();
  bool _isDarkMode = false;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DoorMotor',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
        brightness: Brightness.light,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        brightness: Brightness.dark,
      ),
      themeMode: _isDarkMode ? ThemeMode.dark : ThemeMode.light,
      initialRoute: '/',
      routes: {
        '/': (context) => HomeScreen(ble: _ble, onThemeToggle: () {
          setState(() => _isDarkMode = !_isDarkMode);
        }, isDarkMode: _isDarkMode),
        '/schedule': (context) => ScheduleScreen(ble: _ble),
        '/settings': (context) => SettingsScreen(ble: _ble),
        '/stats': (context) => StatsScreen(),
      },
    );
  }
}