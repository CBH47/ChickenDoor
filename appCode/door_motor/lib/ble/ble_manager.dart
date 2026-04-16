import 'dart:async';
import 'dart:convert';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
 
class BleManager {
  static const String deviceName = "DoorMotor";
 
  // UUIDs matching the Pico firmware
  static const String serviceUuid    = "12345678-1234-5678-1234-56789abcdef0";
  static const String cmdUuid        = "12345678-1234-5678-1234-56789abcdef1";
  static const String statusUuid     = "12345678-1234-5678-1234-56789abcdef2";
  static const String datetimeUuid   = "12345678-1234-5678-1234-56789abcdef3";
  static const String scheduleUuid   = "12345678-1234-5678-1234-56789abcdef4";
  static const String batteryUuid    = "12345678-1234-5678-1234-56789abcdef5";
  static const String deviceNameUuid = "12345678-1234-5678-1234-56789abcdef6";
  static const String timezoneUuid   = "12345678-1234-5678-1234-56789abcdef7";
  static const String firmwareUuid   = "12345678-1234-5678-1234-56789abcdef8";
  static const String settingsUuid   = "12345678-1234-5678-1234-56789abcdef9";
  static const String statsUuid      = "12345678-1234-5678-1234-56789abcdeff";
 
  BluetoothDevice? _device;
  BluetoothCharacteristic? _cmdChar;
  BluetoothCharacteristic? _statusChar;
  BluetoothCharacteristic? _datetimeChar;
  BluetoothCharacteristic? _scheduleChar;
  BluetoothCharacteristic? _batteryChar;
  BluetoothCharacteristic? _deviceNameChar;
  BluetoothCharacteristic? _timezoneChar;
  BluetoothCharacteristic? _firmwareChar;
  BluetoothCharacteristic? _settingsChar;
  BluetoothCharacteristic? _statsChar;
 
  final _statusController   = StreamController<String>.broadcast();
  final _batteryController  = StreamController<String>.broadcast();
  final _rssiController     = StreamController<int>.broadcast();
  final _statsController    = StreamController<String>.broadcast();
 
  Stream<String> get statusStream   => _statusController.stream;
  Stream<String> get batteryStream  => _batteryController.stream;
  Stream<int>    get rssiStream     => _rssiController.stream;
  Stream<String> get statsStream    => _statsController.stream;
 
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
    try {
      // Request larger MTU so stats JSON fits in a single notification packet.
      await device.requestMtu(512);
    } catch (_) {
      // MTU negotiation is best-effort; ignore failures.
    }
    await _discoverServices();
    await _subscribeToNotifications();
    await _syncTime();
    _monitorSignalStrength();
  }
 
  Future<void> _discoverServices() async {
    List<BluetoothService> services = await _device!.discoverServices();
    for (BluetoothService service in services) {
      if (service.uuid.toString() == serviceUuid) {
        for (BluetoothCharacteristic c in service.characteristics) {
          final uuid = c.uuid.toString();
          if (uuid == cmdUuid)        _cmdChar        = c;
          if (uuid == statusUuid)     _statusChar     = c;
          if (uuid == datetimeUuid)   _datetimeChar   = c;
          if (uuid == scheduleUuid)   _scheduleChar   = c;
          if (uuid == batteryUuid)    _batteryChar    = c;
          if (uuid == deviceNameUuid) _deviceNameChar = c;
          if (uuid == timezoneUuid)   _timezoneChar   = c;
          if (uuid == firmwareUuid)   _firmwareChar   = c;
          if (uuid == settingsUuid)   _settingsChar   = c;
          if (uuid == statsUuid)      _statsChar      = c;
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
 
    await _statsChar?.setNotifyValue(true);
    _statsChar?.lastValueStream.listen((value) {
      _statsController.add(utf8.decode(value));
    });
  }
 
  Future<void> _syncTime() async {
    int timestamp = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    await _datetimeChar?.write(utf8.encode(timestamp.toString()));
  }
 
  void _monitorSignalStrength() {
    Future.doWhile(() async {
      if (_device == null) return false;
      try {
        int rssi = await _device!.readRssi();
        _rssiController.add(rssi);
      } catch (e) {
        // device disconnected
      }
      await Future.delayed(const Duration(seconds: 2));
      return _device != null;
    });
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
 
  Future<String> readStats() async {
    List<int>? value = await _statsChar?.read();
    return value != null ? utf8.decode(value) : "{}";
  }
 
  // Settings methods
  Future<String> readDeviceName() async {
    List<int>? value = await _deviceNameChar?.read();
    return value != null ? utf8.decode(value) : "DoorMotor";
  }
 
  Future<void> writeDeviceName(String name) async {
    await _deviceNameChar?.write(utf8.encode(name));
  }
 
  Future<String> readTimezone() async {
    List<int>? value = await _timezoneChar?.read();
    return value != null ? utf8.decode(value) : "UTC";
  }
 
  Future<void> writeTimezone(String timezone) async {
    await _timezoneChar?.write(utf8.encode(timezone));
  }
 
  Future<String> readFirmwareVersion() async {
    List<int>? value = await _firmwareChar?.read();
    return value != null ? utf8.decode(value) : "Unknown";
  }
 
  Future<void> resetSettings() async {
    await _settingsChar?.write(utf8.encode("RESET"));
  }
 
  // Timer methods
  Future<void> sendTimerCommand(int minutes) async {
    await _cmdChar?.write(utf8.encode("TIMER:$minutes"), withoutResponse: false);
  }
 
  Future<void> disconnect() async {
    await _device?.disconnect();
    _device        = null;
    _cmdChar       = null;
    _statusChar    = null;
    _datetimeChar  = null;
    _scheduleChar  = null;
    _batteryChar   = null;
    _deviceNameChar = null;
    _timezoneChar  = null;
    _firmwareChar  = null;
    _settingsChar  = null;
    _statsChar     = null;
  }
 
  void dispose() {
    _statusController.close();
    _batteryController.close();
    _rssiController.close();
    _statsController.close();
  }
}