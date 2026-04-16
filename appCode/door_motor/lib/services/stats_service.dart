import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Stores door-operation statistics locally on the phone.
///
/// Call [init] once after construction, then call [setPendingReason] just
/// before sending a BLE command so the reason is stamped on the event that
/// comes back through [statusStream].
class StatsService extends ChangeNotifier {
  static const List<String> _days = [
    'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun',
  ];
  static const int _maxRecent = 5;

  Map<String, int> _dailyStats = {for (final d in _days) d: 0};
  List<Map<String, dynamic>> _recentActivity = [];
  int _totalOperations = 0;
  String _weekKey = '';
  String? _pendingReason;
  StreamSubscription<String>? _statusSub;

  Map<String, int> get dailyStats => Map.unmodifiable(_dailyStats);
  List<Map<String, dynamic>> get recentActivity =>
      List.unmodifiable(_recentActivity);
  int get totalOperations => _totalOperations;
  double get dailyAverage {
    final sum = _dailyStats.values.fold(0, (a, b) => a + b);
    return sum / _days.length;
  }

  /// Load persisted stats and start listening to [statusStream].
  Future<void> init(Stream<String> statusStream) async {
    await _load();
    _statusSub?.cancel();
    _statusSub = statusStream.listen(_onStatus);
  }

  /// Call this just before sending "OPEN", "CLOSE", or "TIMER:n" so the
  /// reason is attached to the resulting status event.
  void setPendingReason(String reason) {
    _pendingReason = reason;
  }

  /// Erase all stored statistics.
  Future<void> reset() async {
    _dailyStats = {for (final d in _days) d: 0};
    _recentActivity = [];
    _totalOperations = 0;
    _weekKey = _currentWeekKey();
    await _persist();
    notifyListeners();
  }

  // ── internals ────────────────────────────────────────────────────────────

  void _onStatus(String status) {
    if (status == 'OPEN' || status == 'CLOSED') {
      final action = status;
      final reason = _pendingReason ?? 'Schedule';
      _pendingReason = null;
      _record(action, reason);
    } else {
      // Any non-terminal status clears a stale pending reason only if it
      // is clearly unrelated (e.g. ESTOP, BATTERY_CRITICAL, etc).
      if (status != 'OPENING' && status != 'CLOSING') {
        _pendingReason = null;
      }
    }
  }

  void _record(String action, String reason) {
    final now = DateTime.now();
    final week = _currentWeekKey();

    if (_weekKey != week) {
      _dailyStats = {for (final d in _days) d: 0};
      _weekKey = week;
    }

    final dayKey = _days[now.weekday - 1];
    _dailyStats[dayKey] = (_dailyStats[dayKey] ?? 0) + 1;
    _totalOperations++;

    _recentActivity.insert(0, {
      'timestamp': now.millisecondsSinceEpoch ~/ 1000,
      'action': action,
      'reason': reason,
    });
    if (_recentActivity.length > _maxRecent) {
      _recentActivity = _recentActivity.sublist(0, _maxRecent);
    }

    _persist();
    notifyListeners();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    _weekKey = _currentWeekKey();
    final storedWeek = prefs.getString('stats_week_key') ?? '';

    if (storedWeek == _weekKey) {
      final raw = prefs.getString('stats_daily');
      if (raw != null) {
        final decoded = jsonDecode(raw) as Map<String, dynamic>;
        for (final d in _days) {
          _dailyStats[d] = (decoded[d] as num?)?.toInt() ?? 0;
        }
      }
    } else {
      _dailyStats = {for (final d in _days) d: 0};
    }

    _totalOperations = prefs.getInt('stats_total') ?? 0;

    final recentRaw = prefs.getString('stats_recent');
    if (recentRaw != null) {
      final list = jsonDecode(recentRaw) as List<dynamic>;
      _recentActivity = list
          .whereType<Map<String, dynamic>>()
          .take(_maxRecent)
          .toList();
    }
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('stats_week_key', _weekKey);
    await prefs.setString('stats_daily', jsonEncode(_dailyStats));
    await prefs.setString('stats_recent', jsonEncode(_recentActivity));
    await prefs.setInt('stats_total', _totalOperations);
  }

  String _currentWeekKey() {
    final now = DateTime.now();
    final monday = now.subtract(Duration(days: now.weekday - 1));
    return '${monday.year}-${monday.month.toString().padLeft(2, '0')}-'
        '${monday.day.toString().padLeft(2, '0')}';
  }

  @override
  void dispose() {
    _statusSub?.cancel();
    super.dispose();
  }
}
