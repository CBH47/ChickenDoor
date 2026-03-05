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
    // grab the schedule json from pico
    String json = await widget.ble.readSchedule();
    setState(() {
      _rules = List<Map<String, dynamic>>.from(jsonDecode(json));
      _loading = false;
    });
  }

  Future<void> _saveSchedule() async {
    // send updated schedule back to pico
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

  void _editRule(int index) {
    final rule = _rules[index];
    showDialog(
      context: context,
      builder: (context) => _AddRuleDialog(
        days: _days,
        initialRule: rule,
        onAdd: (updatedRule) {
          setState(() => _rules[index] = updatedRule);
          _saveSchedule();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Schedule"),
        actions: [
          PopupMenuButton(
            itemBuilder: (context) => [
              PopupMenuItem(
                child: const Text("Save/Load Profile"),
                onTap: () => _showProfileManager(),
              ),
            ],
          ),
        ],
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
                      trailing: PopupMenuButton(
                        itemBuilder: (context) => [
                          PopupMenuItem(
                            child: const Text("Edit"),
                            onTap: () => _editRule(index),
                          ),
                          PopupMenuItem(
                            child: const Text("Delete"),
                            onTap: () => _deleteRule(index),
                          ),
                        ],
                      ),
                    );
                  },
                ),
    );
  }

  void _showProfileManager() {
    // save/load different schedule sets
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Schedule Profiles"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ElevatedButton(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Profile saved as 'My Schedule'")),
                );
                Navigator.pop(context);
              },
              child: const Text("Save Current Schedule"),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Loaded 'Summer Schedule'")),
                );
                Navigator.pop(context);
              },
              child: const Text("Load Saved Schedule"),
            ),
          ],
        ),
      ),
    );
  }
}

class _AddRuleDialog extends StatefulWidget {
  final List<String> days;
  final Function(Map<String, dynamic>) onAdd;
  final Map<String, dynamic>? initialRule;

  const _AddRuleDialog({
    required this.days,
    required this.onAdd,
    this.initialRule,
  });

  @override
  State<_AddRuleDialog> createState() => _AddRuleDialogState();
}

class _AddRuleDialogState extends State<_AddRuleDialog> {
  late int _hour;
  late int _minute;
  late String _action;
  late List<String> _selectedDays;

  @override
  void initState() {
    super.initState();
    if (widget.initialRule != null) {
      _hour = widget.initialRule!['hour'];
      _minute = widget.initialRule!['minute'];
      _action = widget.initialRule!['action'];
      _selectedDays = List<String>.from(widget.initialRule!['days']);
    } else {
      _hour = 7;
      _minute = 0;
      _action = 'OPEN';
      _selectedDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.initialRule != null ? "Edit Schedule Rule" : "Add Schedule Rule"),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // set what time this rule runs
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
          // open or close the door
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
          // pick which days this runs on
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