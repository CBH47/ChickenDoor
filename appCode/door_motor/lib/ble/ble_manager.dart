import 'dart:async';
import 'dart:convert';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

class BleManager {
  static const String deviceName = "DoorMotor";

  // UUIDs matching the Pico firmware
  static const String serviceUuid     = "12345678-1234-5678-1234-56789abcdef0";
  static const String cmdUuid         = "12345678-1234-5678-1234-56789abcdef1";
  static const String statusUuid      = "12345678-1234-5678-1234-56789abcdef2";
  static const String datetimeUuid    = "12345678-1234-5678-1234-56789abcdef3";
  static const String scheduleUuid    = "12345678-1234-5678-1234-56789abcdef4";
  static const String batteryUuid     = "12345678-1234-5678-1234-56789abcdef5";

  BluetoothDevice? _device;
  BluetoothCharacteristic? _cmdChar;
  BluetoothCharacteristic? _statusChar;
  BluetoothCharacteristic? _datetimeChar;
  BluetoothCharacteristic? _scheduleChar;
  BluetoothCharacteristic? _batteryChar;

  final _statusController  = StreamController<String>.broadcast();
  final _batteryController = StreamController<String>.broadcast();

  Stream<String> get statusStream  => _statusController.stream;
  Stream<String> get batteryStream => _batteryController.stream;

  bool get isConnected => _device != null;

  Future<void> startScan(Function(BluetoothDevice) onFound) async {
    await FlutterBluePlus.startScan(timeout: const Duration(seconds: 10));
    FlutterBluePlus.scanResults.listen((results) {
      for (ScanResult r in results) {
        if (r.device.platformName == deviceName) {
          FlutterBluePlus.stopScan();
          onFound(r.device);
        }
      }
    });
  }

  Future<void> connect(BluetoothDevice device) async {
    _device = device;
    await device.connect(autoConnect: false);
    await _discoverServices();
    await _subscribeToNotifications();
    await _syncTime();
  }

  Future<void> _discoverServices() async {
    List<BluetoothService> services = await _device!.discoverServices();
    for (BluetoothService service in services) {
      if (service.uuid.toString() == serviceUuid) {
        for (BluetoothCharacteristic c in service.characteristics) {
          String uuid = c.uuid.toString();
          if (uuid == cmdUuid)      _cmdChar      = c;
          if (uuid == statusUuid)   _statusChar   = c;
          if (uuid == datetimeUuid) _datetimeChar = c;
          if (uuid == scheduleUuid) _scheduleChar = c;
          if (uuid == batteryUuid)  _batteryChar  = c;
        }
      }
    }
  }

  Future<void> _subscribeToNotifications() async {
    await _statusChar?.setNotifyValue(true);
    _statusChar?.lastValueStream.listen((value) {
      _statusController.add(utf8.decode(value));
    });

    await _batteryChar?.setNotifyValue(true);
    _batteryChar?.lastValueStream.listen((value) {
      _batteryController.add(utf8.decode(value));
    });
  }

  Future<void> _syncTime() async {
    // Write current Unix timestamp to datetime characteristic
    int timestamp = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    await _datetimeChar?.write(utf8.encode(timestamp.toString()));
  }

  Future<void> sendCommand(String command) async {
    await _cmdChar?.write(utf8.encode(command), withoutResponse: false);
  }

  Future<String> readSchedule() async {
    List<int>? value = await _scheduleChar?.read();
    return value != null ? utf8.decode(value) : "[]";
  }

  Future<void> writeSchedule(String json) async {
    await _scheduleChar?.write(utf8.encode(json));
  }

  Future<void> disconnect() async {
    await _device?.disconnect();
    _device = null;
    _cmdChar = null;
    _statusChar = null;
    _datetimeChar = null;
    _scheduleChar = null;
    _batteryChar = null;
  }

  void dispose() {
    _statusController.close();
    _batteryController.close();
  }
}