import 'package:flutter/material.dart';
import '../ble/ble_manager.dart';
import 'dart:convert';

class ScheduleScreen extends StatefulWidget {
  final BleManager ble;
  const ScheduleScreen({super.key, required this.ble});

  @override
  State<ScheduleScreen> createState() => _ScheduleScreenState();
}

class _ScheduleScreenState extends State<ScheduleScreen> {
  List<Map<String, dynamic>> _rules = [];
  bool _loading = true;

  final List<String> _days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  @override
  void initState() {
    super.initState();
    _loadSchedule();
  }

  Future<void> _loadSchedule() async {
    String json = await widget.ble.readSchedule();
    setState(() {
      _rules = List<Map<String, dynamic>>.from(jsonDecode(json));
      _loading = false;
    });
  }

  Future<void> _saveSchedule() async {
    await widget.ble.writeSchedule(jsonEncode(_rules));
  }

  void _addRule() {
    showDialog(
      context: context,
      builder: (context) => _AddRuleDialog(
        days: _days,
        onAdd: (rule) {
          setState(() => _rules.add(rule));
          _saveSchedule();
        },
      ),
    );
  }

  void _deleteRule(int index) {
    setState(() => _rules.removeAt(index));
    _saveSchedule();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Schedule"),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addRule,
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _rules.isEmpty
              ? const Center(child: Text("No scheduled rules yet.\nTap + to add one."))
              : ListView.builder(
                  itemCount: _rules.length,
                  itemBuilder: (context, index) {
                    final rule = _rules[index];
                    return ListTile(
                      leading: Icon(
                        rule['action'] == 'OPEN'
                            ? Icons.arrow_upward
                            : Icons.arrow_downward,
                        color: rule['action'] == 'OPEN'
                            ? Colors.green
                            : Colors.red,
                      ),
                      title: Text(
                        "${rule['action']} at ${rule['hour'].toString().padLeft(2, '0')}:${rule['minute'].toString().padLeft(2, '0')}",
                      ),
                      subtitle: Text(
                        (rule['days'] as List).join(', '),
                      ),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete),
                        onPressed: () => _deleteRule(index),
                      ),
                    );
                  },
                ),
    );
  }
}

class _AddRuleDialog extends StatefulWidget {
  final List<String> days;
  final Function(Map<String, dynamic>) onAdd;

  const _AddRuleDialog({required this.days, required this.onAdd});

  @override
  State<_AddRuleDialog> createState() => _AddRuleDialogState();
}

class _AddRuleDialogState extends State<_AddRuleDialog> {
  int _hour = 7;
  int _minute = 0;
  String _action = 'OPEN';
  final List<String> _selectedDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text("Add Schedule Rule"),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Time picker
          Row(
            children: [
              const Text("Time: "),
              DropdownButton<int>(
                value: _hour,
                items: List.generate(24, (i) => DropdownMenuItem(
                  value: i,
                  child: Text(i.toString().padLeft(2, '0')),
                )),
                onChanged: (v) => setState(() => _hour = v!),
              ),
              const Text(" : "),
              DropdownButton<int>(
                value: _minute,
                items: [0, 15, 30, 45].map((m) => DropdownMenuItem(
                  value: m,
                  child: Text(m.toString().padLeft(2, '0')),
                )).toList(),
                onChanged: (v) => setState(() => _minute = v!),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Action picker
          Row(
            children: [
              const Text("Action: "),
              DropdownButton<String>(
                value: _action,
                items: ['OPEN', 'CLOSE'].map((a) => DropdownMenuItem(
                  value: a,
                  child: Text(a),
                )).toList(),
                onChanged: (v) => setState(() => _action = v!),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Day selector
          Wrap(
            spacing: 4,
            children: widget.days.map((day) {
              final selected = _selectedDays.contains(day);
              return FilterChip(
                label: Text(day),
                selected: selected,
                onSelected: (val) {
                  setState(() {
                    if (val) {
                      _selectedDays.add(day);
                    } else {
                      _selectedDays.remove(day);
                    }
                  });
                },
              );
            }).toList(),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text("Cancel"),
        ),
        ElevatedButton(
          onPressed: () {
            widget.onAdd({
              'hour': _hour,
              'minute': _minute,
              'action': _action,
              'days': _selectedDays,
            });
            Navigator.pop(context);
          },
          child: const Text("Add"),
        ),
      ],
    );
  }
}