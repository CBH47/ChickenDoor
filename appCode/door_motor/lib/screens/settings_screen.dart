import 'package:flutter/material.dart';
import '../ble/ble_manager.dart';

class SettingsScreen extends StatefulWidget {
  final BleManager ble;
  const SettingsScreen({super.key, required this.ble});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late BleManager _ble;
  late TextEditingController _deviceNameController;
  
  String _firmwareVersion = "Loading...";
  String _selectedTimezone = "UTC";
  bool _isLoading = true;
  bool _isSaving = false;

  final List<String> _timezones = [
    "UTC",
    "EST",
    "CST",
    "MST",
    "PST",
    "GMT",
    "CET",
    "IST",
    "JST",
    "AEST",
  ];

  @override
  void initState() {
    super.initState();
    _ble = widget.ble;
    _deviceNameController = TextEditingController();
    _loadSettings();
  }

  @override
  void dispose() {
    _deviceNameController.dispose();
    super.dispose();
  }

  Future<void> _loadSettings() async {
    try {
      // grab device name from pico
      String deviceName = await _ble.readDeviceName();
      _deviceNameController.text = deviceName;

      // grab timezone setting
      String timezone = await _ble.readTimezone();
      if (_timezones.contains(timezone)) {
        _selectedTimezone = timezone;
      }

      // grab firmware version
      String firmware = await _ble.readFirmwareVersion();
      
      setState(() {
        _firmwareVersion = firmware;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error loading settings: $e")),
        );
      }
    }
  }

  Future<void> _saveSettings() async {
    setState(() => _isSaving = true);
    try {
      // push device name to pico
      await _ble.writeDeviceName(_deviceNameController.text);
      
      // push timezone to pico
      await _ble.writeTimezone(_selectedTimezone);

      setState(() => _isSaving = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Settings saved successfully")),
        );
      }
    } catch (e) {
      setState(() => _isSaving = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error saving settings: $e")),
        );
      }
    }
  }

  Future<void> _resetSettings() async {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Reset Settings?"),
        content: const Text("factory reset inbound - all settings gone. can't undo this."),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancel"),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              setState(() => _isSaving = true);
              try {
                // nuke it from orbit - factory reset
                await _ble.resetSettings();
                setState(() => _isSaving = false);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("Settings reset to factory defaults")),
                  );
                  _loadSettings();
                }
              } catch (e) {
                setState(() => _isSaving = false);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("Error resetting settings: $e")),
                  );
                }
              }
            },
            child: const Text("Reset", style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Settings"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Device stuff like firmware version
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Device Information",
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 16),
                          // check what firmware's running on the pico
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text("Firmware Version:"),
                              Text(
                                _firmwareVersion,
                                style: const TextStyle(fontWeight: FontWeight.w600),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Settings Section
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Configuration",
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 16),

                          // what the door shows up as when scanning for ble devices
                          TextField(
                            controller: _deviceNameController,
                            decoration: InputDecoration(
                              labelText: "Device Name",
                              hintText: "e.g., Chicken Door",
                              border: OutlineInputBorder(),
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 12,
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),

                          // where the door is so schedules run at the right time
                          DropdownButtonFormField<String>(
                            value: _selectedTimezone,
                            decoration: InputDecoration(
                              labelText: "Timezone",
                              border: OutlineInputBorder(),
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 12,
                              ),
                            ),
                            items: _timezones.map((tz) {
                              return DropdownMenuItem(
                                value: tz,
                                child: Text(tz),
                              );
                            }).toList(),
                            onChanged: (value) {
                              if (value != null) {
                                setState(() => _selectedTimezone = value);
                              }
                            },
                          ),
                          const SizedBox(height: 24),

                          // push all changes to the door
                          ElevatedButton.icon(
                            onPressed: _isSaving ? null : _saveSettings,
                            icon: _isSaving
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Icon(Icons.save),
                            label: Text(_isSaving ? "Saving..." : "Save Settings"),
                            style: ElevatedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),

                  // WARNING: here be dragons
                  Card(
                    color: Colors.red.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Danger Zone",
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: Colors.red,
                            ),
                          ),
                          const SizedBox(height: 16),
                          OutlinedButton.icon(
                            onPressed: _isSaving ? null : _resetSettings,
                            icon: const Icon(Icons.restart_alt),
                            label: const Text("Reset to Factory Defaults"),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.red,
                              side: const BorderSide(color: Colors.red),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 32),
                ],
              ),
            ),
    );
  }
}
