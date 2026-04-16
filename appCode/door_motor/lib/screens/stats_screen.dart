import 'package:flutter/material.dart';
import '../services/stats_service.dart';

class StatsScreen extends StatefulWidget {
  final StatsService stats;
  const StatsScreen({super.key, required this.stats});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  static const List<String> _days = [
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sat',
    'Sun',
  ];

  @override
  void initState() {
    super.initState();
    widget.stats.addListener(_onStatsChanged);
  }

  void _onStatsChanged() {
    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _resetStats() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Reset Statistics'),
        content: const Text(
          'This will erase all locally stored stats. This cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text('Reset', style: TextStyle(color: Colors.red.shade700)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await widget.stats.reset();
    }
  }

  String _formatEventTime(int epochSeconds) {
    if (epochSeconds <= 0) return 'Unknown time';
    final dt = DateTime.fromMillisecondsSinceEpoch(epochSeconds * 1000);
    final hh = dt.hour.toString().padLeft(2, '0');
    final mm = dt.minute.toString().padLeft(2, '0');
    return '${dt.month}/${dt.day} at $hh:$mm';
  }

  @override
  void dispose() {
    widget.stats.removeListener(_onStatsChanged);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dailyStats = widget.stats.dailyStats;
    final recentActivity = widget.stats.recentActivity;
    final totalOperations = widget.stats.totalOperations;
    final dailyAverage = widget.stats.dailyAverage;

    final maxCount = dailyStats.values.isEmpty
        ? 1.0
        : dailyStats.values.reduce((a, b) => a > b ? a : b).toDouble();
    final todayKey = _days[DateTime.now().weekday - 1];
    final todayCount = dailyStats[todayKey] ?? 0;
    final avgStr = dailyAverage.toStringAsFixed(1);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Daily Statistics'),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline),
            tooltip: 'Reset stats',
            onPressed: _resetStats,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: _statCard('Total Today', '$todayCount')),
                const SizedBox(width: 16),
                Expanded(child: _statCard('Weekly Avg', avgStr)),
                const SizedBox(width: 16),
                Expanded(child: _statCard('All Time', '$totalOperations')),
              ],
            ),
            const SizedBox(height: 32),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Door Operations Per Day',
                      style: Theme.of(context).textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 24),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: _days.map((day) {
                        final count = dailyStats[day] ?? 0;
                        final height = maxCount > 0
                            ? (count / maxCount * 150).toDouble()
                            : 0.0;
                        final isToday = day == todayKey;
                        return Column(
                          children: [
                            Container(
                              width: 35,
                              height: height.clamp(4.0, 150.0),
                              decoration: BoxDecoration(
                                color: isToday
                                    ? Theme.of(context).colorScheme.primary
                                    : Theme.of(context)
                                        .colorScheme
                                        .primary
                                        .withOpacity(0.4),
                                borderRadius: BorderRadius.circular(4),
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              '$count',
                              style: Theme.of(context).textTheme.bodySmall
                                  ?.copyWith(fontWeight: FontWeight.bold),
                            ),
                            Text(
                              day,
                              style: Theme.of(context).textTheme.labelSmall,
                            ),
                          ],
                        );
                      }).toList(),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Recent Activity',
                      style: Theme.of(context).textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    if (recentActivity.isEmpty)
                      Text(
                        'No recent activity yet.',
                        style: Theme.of(context).textTheme.bodyMedium,
                      )
                    else
                      ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: recentActivity.length,
                        separatorBuilder: (_, __) => const Divider(),
                        itemBuilder: (context, index) {
                          final event = recentActivity[index];
                          final isOpen = event['action'] == 'OPEN';
                          return Padding(
                            padding: const EdgeInsets.symmetric(vertical: 8.0),
                            child: Row(
                              children: [
                                Icon(
                                  isOpen
                                      ? Icons.arrow_upward
                                      : Icons.arrow_downward,
                                  color: isOpen ? Colors.green : Colors.red,
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        "${event['action']} - ${event['reason']}",
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodyMedium
                                            ?.copyWith(
                                              fontWeight: FontWeight.w600,
                                            ),
                                      ),
                                      Text(
                                        _formatEventTime(
                                          event['timestamp'] as int,
                                        ),
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodySmall,
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _statCard(String label, String value) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text(label, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.displaySmall
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }
}
