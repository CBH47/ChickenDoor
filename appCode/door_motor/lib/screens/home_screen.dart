import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import '../ble/ble_manager.dart';
import '../services/notification_service.dart';

class HomeScreen extends StatefulWidget {
  final BleManager ble;
  final VoidCallback onThemeToggle;
  final bool isDarkMode;
  const HomeScreen({
    super.key,
    required this.ble,
    required this.onThemeToggle,
    required this.isDarkMode,
  });

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
    setState(() {
      final newDoorState = _getDoorState();
      // check if door state actually changed
      if (_previousDoorState.isNotEmpty && _previousDoorState != newDoorState) {
        if (newDoorState == "OPEN") {
          _notificationService.showDoorOpenNotification();
        } else if (newDoorState == "CLOSED") {
          _notificationService.showDoorCloseNotification();
        } else if (newDoorState == "UNKNOWN") {
          _notificationService.showUnexpectedStateNotification(status);
        }
      }
      _previousDoorState = newDoorState;
      _status = status;
    });
  });
  _ble.batteryStream.listen((battery) {
    if (battery.contains("CRITICAL") || battery.contains("LOW")) {
      _notificationService.showBatteryWarningNotification();
    }
    setState(() => _battery = battery); // update batt display
  });
  _ble.overrideStream.listen((override) {
    setState(() => _override = override);
  });
  _ble.rssiStream.listen((rssi) {
    setState(() => _rssi = rssi);
  });
}

  String _status = "Disconnected";
  String _battery = "--";
  String _override = "NONE";
  bool _isConnected = false;
  bool _isScanning = false;
  int _rssi = 0;  // Signal strength
  int _timerMinutes = 0;  // Active timer (0 = no timer)
  String _previousDoorState = "";  // Track door state changes for notifications
  final NotificationService _notificationService = NotificationService();

  // Helper method to parse door state from status
  String _getDoorState() {
    if (_status.contains("OPEN")) {
      return "OPEN";
    } else if (_status.contains("CLOSED")) {
      return "CLOSED";
    } else if (_status.contains("MOVING")) {
      return "MOVING";
    }
    return "UNKNOWN"; // dunno what the door's doing
  }

  // Helper method to get color based on door state
  Color _getDoorStateColor() {
    String state = _getDoorState();
    if (state == "OPEN") return Colors.green;
    if (state == "CLOSED") return Colors.orange;
    if (state == "MOVING") return Colors.blue;
    return Colors.grey;
  }

  // Helper method to get icon based on door state
  IconData _getDoorStateIcon() {
    String state = _getDoorState();
    if (state == "OPEN") return Icons.arrow_upward;
    if (state == "CLOSED") return Icons.arrow_downward;
    if (state == "MOVING") return Icons.autorenew;
    return Icons.help;
  }

  // Helper method to check if override is active
  bool _isOverrideActive() {
    return _override != "NONE" && _override.isNotEmpty;
  }

  // Helper method to get override display text
  String _getOverrideText() {
    if (_override == "KEEP_OPEN") return "Door Locked OPEN";
    if (_override == "KEEP_CLOSED") return "Door Locked CLOSED";
    return "No Override";
  }

  // Helper method to get override color
  Color _getOverrideColor() {
    if (_override == "KEEP_OPEN") return Colors.blue;
    if (_override == "KEEP_CLOSED") return Colors.blue;
    return Colors.grey;
  }

  // Helper method to get signal strength description
  String _getSignalStrength() {
    if (_rssi == 0) return "Unknown";
    if (_rssi > -50) return "Excellent";
    if (_rssi > -60) return "Good";
    if (_rssi > -70) return "Fair";
    return "Weak";
  }

  // Helper method to get signal strength color
  Color _getSignalColor() {
    if (_rssi == 0) return Colors.grey;
    if (_rssi > -60) return Colors.green;
    if (_rssi > -70) return Colors.orange;
    return Colors.red;
  }

  // Timer dialog helper
  void _showTimerDialog() {
    showDialog(
      context: context,
      builder: (context) => _TimerPickerDialog(
        onTimerSelected: (minutes) {
          _ble.sendTimerCommand(minutes);
          setState(() => _timerMinutes = minutes);
          // Reset timer after specified time (for UI countdown)
          Future.delayed(Duration(minutes: minutes), () {
            if (mounted) {
              setState(() => _timerMinutes = 0);
            }
          });
        },
      ),
    );
  }

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

  Future<void> _emergencyStop() async {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Emergency Stop"),
        content: const Text("This will immediately stop the motor. Are you sure?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () {
              _ble.sendCommand("STOP");
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("Motor stopped")),
              );
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text("Stop Motor"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("DoorMotor"),
        centerTitle: false,
        actions: [
          // Dark mode toggle
          IconButton(
            icon: Icon(widget.isDarkMode ? Icons.light_mode : Icons.dark_mode),
            onPressed: widget.onThemeToggle,
            tooltip: "Toggle dark mode",
          ),
          // Stats button
          IconButton(
            icon: const Icon(Icons.bar_chart),
            onPressed: () {
              Navigator.pushNamed(context, '/stats');
            },
            tooltip: "View statistics",
          ),
          // Connection Status Badge
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
            child: Center(
              child: Tooltip(
                message: _isConnected
                    ? "Connected • Signal: ${_getSignalStrength()}"
                    : "Not Connected",
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: _isConnected
                        ? Colors.green.withOpacity(0.15)
                        : Colors.red.withOpacity(0.15),
                    border: Border.all(
                      color: _isConnected ? Colors.green : Colors.red,
                      width: 2,
                    ),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 10,
                        height: 10,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: _isConnected ? Colors.green : Colors.red,
                          boxShadow: _isConnected
                              ? [
                                  BoxShadow(
                                    color: Colors.green.withOpacity(0.6),
                                    blurRadius: 8,
                                    spreadRadius: 2,
                                  )
                                ]
                              : [],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _isConnected ? "Connected" : "Offline",
                        style: TextStyle(
                          color: _isConnected ? Colors.green : Colors.red,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          // Settings icon
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.pushNamed(context, '/settings');
            },
          ),
          // Disconnect button (only when connected)
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
            // Door Status Card - Large and prominent
            Card(
              color: _getDoorStateColor().withOpacity(0.15),
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(32.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Large door state icon
                    Icon(
                      _getDoorStateIcon(),
                      size: 64,
                      color: _getDoorStateColor(),
                    ),
                    const SizedBox(height: 24),
                    // Door state text
                    Text(
                      _getDoorState(),
                      style: Theme.of(context).textTheme.displaySmall?.copyWith(
                            color: _getDoorStateColor(),
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    const SizedBox(height: 16),
                    // Connection status
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          _isConnected ? Icons.bluetooth_connected : Icons.bluetooth_disabled,
                          color: _isConnected ? Colors.blue : Colors.grey,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          _isConnected ? "Connected" : "Disconnected",
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    // Battery status
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.battery_std,
                          color: Colors.grey,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          "Battery: $_battery",
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                    if (_isConnected) ...[
                      const SizedBox(height: 12),
                      // Signal Strength
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.signal_cellular_alt,
                            color: _getSignalColor(),
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            "Signal: ${_getSignalStrength()}",
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: _getSignalColor(),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),

            // Override Status Card - Show override state if connected
            if (_isConnected)
              Card(
                color: _isOverrideActive() ? _getOverrideColor().withOpacity(0.15) : Colors.grey.withOpacity(0.05),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      Text(
                        "Override Control",
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _getOverrideText(),
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: _getOverrideColor(),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 16),
                      // Override buttons
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: () => _ble.setOverride("KEEP_OPEN"),
                              icon: const Icon(Icons.lock_open),
                              label: const Text("Lock Open"),
                              style: OutlinedButton.styleFrom(
                                foregroundColor: Colors.green,
                                side: const BorderSide(color: Colors.green),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: () => _ble.setOverride("KEEP_CLOSED"),
                              icon: const Icon(Icons.lock),
                              label: const Text("Lock Closed"),
                              style: OutlinedButton.styleFrom(
                                foregroundColor: Colors.orange,
                                side: const BorderSide(color: Colors.orange),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: _isOverrideActive() ? () => _ble.clearOverride() : null,
                          icon: const Icon(Icons.lock_outline),
                          label: const Text("Clear Override"),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.red,
                            side: BorderSide(
                              color: _isOverrideActive() ? Colors.red : Colors.grey,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 24),

            // Timer Card - Quick timer for auto-close
            if (_isConnected)
              Card(
                color: _timerMinutes > 0 ? Colors.blue.withOpacity(0.15) : Colors.grey.withOpacity(0.05),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      Text(
                        "Quick Timer",
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 12),
                      if (_timerMinutes > 0)
                        Column(
                          children: [
                            Icon(
                              Icons.timer,
                              size: 32,
                              color: Colors.blue,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              "Door will auto-close in $_timerMinutes min",
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: Colors.blue,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        )
                      else
                        Text(
                          "Open door for a set time",
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _showTimerDialog,
                          icon: const Icon(Icons.schedule),
                          label: const Text("Set Timer"),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.blue,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
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
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _emergencyStop,
                icon: const Icon(Icons.emergency),
                label: const Text("E-STOP"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red.shade700,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _TimerPickerDialog extends StatefulWidget {
  final Function(int) onTimerSelected;
  const _TimerPickerDialog({required this.onTimerSelected});

  @override
  State<_TimerPickerDialog> createState() => _TimerPickerDialogState();
}

class _TimerPickerDialogState extends State<_TimerPickerDialog> {
  int _selectedMinutes = 5;
  
  final List<int> _presets = [5, 15, 30, 60, 120];

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text("Set Timer"),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            "Door will open and auto-close in $_selectedMinutes minutes",
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          // Preset buttons
          Wrap(
            spacing: 8,
            alignment: WrapAlignment.center,
            children: _presets.map((minutes) {
              return ChoiceChip(
                label: Text("$minutes min"),
                selected: _selectedMinutes == minutes,
                onSelected: (selected) {
                  if (selected) {
                    setState(() => _selectedMinutes = minutes);
                  }
                },
              );
            }).toList(),
          ),
          const SizedBox(height: 24),
          // Custom input
          TextField(
            decoration: InputDecoration(
              labelText: "Custom duration (minutes)",
              border: OutlineInputBorder(),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              suffixIcon: IconButton(
                icon: const Icon(Icons.check),
                onPressed: () {
                  // Will be handled by text field below
                },
              ),
            ),
            keyboardType: TextInputType.number,
            onChanged: (value) {
              int? parsed = int.tryParse(value);
              if (parsed != null && parsed > 0) {
                setState(() => _selectedMinutes = parsed);
              }
            },
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text("Cancel"),
        ),
        ElevatedButton.icon(
          onPressed: () {
            widget.onTimerSelected(_selectedMinutes);
            Navigator.pop(context);
          },
          icon: const Icon(Icons.timer),
          label: const Text("Start Timer"),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.blue,
            foregroundColor: Colors.white,
          ),
        ),
      ],
    );
  }
}