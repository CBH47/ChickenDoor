import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import '../ble/ble_manager.dart';

class HomeScreen extends StatefulWidget {
  final BleManager ble;
  const HomeScreen({super.key, required this.ble});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}
class _HomeScreenState extends State<HomeScreen> {
  late BleManager _ble;

  @override
  void initState() {
    print("DEBUG_CHECK: VERSION_ALPHA_1");
  super.initState();
  _ble = widget.ble;
  _ble.statusStream.listen((status) {
    setState(() => _status = status);
  });
  _ble.batteryStream.listen((battery) {
    setState(() => _battery = battery);
  });
}

  String _status = "Disconnected";
  String _battery = "--";
  bool _isConnected = false;
  bool _isScanning = false;

  @override
  void dispose() {
    _ble.dispose();
    super.dispose();
  }

  Future<void> _scan() async {
    setState(() {
      _isScanning = true;
      _status = "Scanning...";
    });

    await _ble.startScan((BluetoothDevice device) async {
      await _ble.connect(device);
      setState(() {
        _isConnected = true;
        _isScanning = false;
        _status = "Connected";
      });
    });

    setState(() => _isScanning = false);
  }

  Future<void> _sendCommand(String command) async {
    if (!_isConnected) return;
    await _ble.sendCommand(command);
  }

  Future<void> _disconnect() async {
    await _ble.disconnect();
    setState(() {
      _isConnected = false;
      _status = "Disconnected";
      _battery = "--";
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("DoorMotor"),
        actions: [
          if (_isConnected)
            IconButton(
              icon: const Icon(Icons.bluetooth_disabled),
              onPressed: _disconnect,
            )
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Status card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Text(
                      "Status",
                      style: Theme.of(context).textTheme.labelLarge,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _status,
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(height: 8),
                    Text("Battery: $_battery"),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 32),

            // Connect button
            if (!_isConnected)
              ElevatedButton.icon(
                onPressed: _isScanning ? null : _scan,
                icon: _isScanning
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.bluetooth),
                label: Text(_isScanning ? "Scanning..." : "Connect"),
              ),

            // Open/Close buttons
            if (_isConnected) ...[
              ElevatedButton.icon(
                onPressed: () => _sendCommand("OPEN"),
                icon: const Icon(Icons.arrow_upward),
                label: const Text("OPEN"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () => _sendCommand("CLOSE"),
                icon: const Icon(Icons.arrow_downward),
                label: const Text("CLOSE"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: () {
                  Navigator.pushNamed(context, '/schedule');
                },
                icon: const Icon(Icons.schedule),
                label: const Text("Manage Schedule"),
              ),
            ],
          ],
        ),
      ),
    );
  }
}