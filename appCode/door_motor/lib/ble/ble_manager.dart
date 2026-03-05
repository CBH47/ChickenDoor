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
  static const String deviceNameUuid  = "12345678-1234-5678-1234-56789abcdef6";
  static const String timezoneUuid    = "12345678-1234-5678-1234-56789abcdef7";
  static const String firmwareUuid    = "12345678-1234-5678-1234-56789abcdef8";
  static const String settingsUuid    = "12345678-1234-5678-1234-56789abcdef9";
  static const String overrideUuid    = "12345678-1234-5678-1234-56789abcdefa"; // these need to match pico

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
  BluetoothCharacteristic? _overrideChar;

  final _statusController  = StreamController<String>.broadcast();
  final _batteryController = StreamController<String>.broadcast();
  final _overrideController = StreamController<String>.broadcast();
  final _rssiController = StreamController<int>.broadcast(); // signal strength updates

  Stream<String> get statusStream  => _statusController.stream;
  Stream<String> get batteryStream => _batteryController.stream;
  Stream<String> get overrideStream => _overrideController.stream;
  Stream<int> get rssiStream => _rssiController.stream; // ble signal

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
    _monitorSignalStrength();
  }

  Future<void> _discoverServices() async {
    List<BluetoothService> services = await _device!.discoverServices();
    for (BluetoothService service in services) {
      if (service.uuid.toString() == serviceUuid) {
        for (BluetoothCharacteristic c in service.characteristics) {
          String uuid = c.uuid.toString();
          if (uuid == cmdUuid)         _cmdChar        = c;
          if (uuid == statusUuid)      _statusChar     = c;
          if (uuid == datetimeUuid)    _datetimeChar   = c;
          if (uuid == scheduleUuid)    _scheduleChar   = c;
          if (uuid == batteryUuid)     _batteryChar    = c;
          if (uuid == deviceNameUuid)  _deviceNameChar = c;
          if (uuid == timezoneUuid)    _timezoneChar   = c;
          if (uuid == firmwareUuid)    _firmwareChar   = c;
          if (uuid == settingsUuid)    _settingsChar   = c;
          if (uuid == overrideUuid)    _overrideChar   = c;
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

    await _overrideChar?.setNotifyValue(true);
    _overrideChar?.lastValueStream.listen((value) {
      _overrideController.add(utf8.decode(value));
    });
  }

  Future<void> _syncTime() async {
    // Write current Unix timestamp to datetime characteristic
    int timestamp = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    await _datetimeChar?.write(utf8.encode(timestamp.toString()));
  }

  void _monitorSignalStrength() {
    // Periodically read RSSI every 2 seconds
    Future.doWhile(() async {
      if (_device == null) return false;
      try {
        int rssi = await _device!.readRssi(); // check signal every 2s
        _rssiController.add(rssi);
      } catch (e) {
        // Device disconnected or smth went wrong
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

  // Settings methods
  Future<String> readDeviceName() async {
    // get the device's bluetooth name
    List<int>? value = await _deviceNameChar?.read();
    return value != null ? utf8.decode(value) : "DoorMotor";
  }

  Future<void> writeDeviceName(String name) async {
    // set the device's name for ble discovery
    await _deviceNameChar?.write(utf8.encode(name));
  }

  Future<String> readTimezone() async {
    // get timezone offset from device, like "-5" for EST
    List<int>? value = await _timezoneChar?.read();
    return value != null ? utf8.decode(value) : "UTC";
  }

  Future<void> writeTimezone(String timezone) async {
    // write timezone offset back to pico
    await _timezoneChar?.write(utf8.encode(timezone));
  }

  Future<String> readFirmwareVersion() async {
    // check what firmware version the pico's running
    List<int>? value = await _firmwareChar?.read();
    return value != null ? utf8.decode(value) : "Unknown";
  }

  Future<void> resetSettings() async {
    // factory reset - nukes all config on pico
    await _settingsChar?.write(utf8.encode("RESET"));
  }

  // Override methods
  Future<void> setOverride(String mode) async {
    // mode can be "KEEP_OPEN", "KEEP_CLOSED", or "NONE" - lock the door in place
    await _overrideChar?.write(utf8.encode(mode), withoutResponse: false);
  }

  Future<void> clearOverride() async {
    // clear the override, back to normal
    await _overrideChar?.write(utf8.encode("NONE"), withoutResponse: false);
  }

  // Timer methods
  Future<void> sendTimerCommand(int minutes) async {
    // Send timer command in format "TIMER:minutes"
    // e.g., "TIMER:15" opens door for 15 mins then auto-closes
    await _cmdChar?.write(utf8.encode("TIMER:$minutes"), withoutResponse: false);
  }

  Future<void> disconnect() async {
    await _device?.disconnect();
    _device = null;
    _cmdChar = null;
    _statusChar = null;
    _datetimeChar = null;
    _scheduleChar = null;
    _batteryChar = null;
    _deviceNameChar = null;
    _timezoneChar = null;
    _firmwareChar = null;
    _settingsChar = null;
    _overrideChar = null;
  }

  void dispose() {
    _statusController.close();
    _batteryController.close();
    _overrideController.close();
    _rssiController.close();
  }
}