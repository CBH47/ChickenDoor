import 'package:flutter/material.dart';

class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  // TODO: replace with real data from BLE when ready
  final Map<String, int> _dailyStats = {
    'Mon': 12,
    'Tue': 15,
    'Wed': 8,
    'Thu': 10,
    'Fri': 14,
    'Sat': 6,
    'Sun': 9,
  };

  @override
  Widget build(BuildContext context) {
    final maxCount = _dailyStats.values.reduce((a, b) => a > b ? a : b).toDouble();
    final totalCount = _dailyStats.values.reduce((a, b) => a + b);
    final avgCount = (totalCount / _dailyStats.length).round();

    return Scaffold(
      appBar: AppBar(
        title: const Text("Daily Statistics"),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // quick stats overview
            SizedBox(
              width: double.infinity,
              child: Row(
                children: [
                Expanded(
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        children: [
                          Text(
                            "Total Today",
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            "${_dailyStats['Sun']}",
                            style: Theme.of(context).textTheme.displaySmall?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        children: [
                          Text(
                            "Weekly Avg",
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            "$avgCount",
                            style: Theme.of(context).textTheme.displaySmall?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
              ),
            ),

            const SizedBox(height: 32),

            // chart showing daily operations
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "Door Operations Per Day",
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: _dailyStats.entries.map((entry) {
                        final height = (entry.value / maxCount * 150).toDouble();
                        return Column(
                          children: [
                            // Bar
                            Container(
                              width: 35,
                              height: height,
                              decoration: BoxDecoration(
                                color: Colors.blue,
                                borderRadius: BorderRadius.circular(4),
                              ),
                            ),
                            const SizedBox(height: 8),
                            // Value
                            Text(
                              "${entry.value}",
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            // Day label
                            Text(
                              entry.key,
                              style: Theme.of(context).textTheme.labelSmall,
                            ),
                          ],
                        );
                      }).toList(),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),

            // recent door events
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "Recent Activity",
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    ListView.separated(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: 5,
                      separatorBuilder: (_, __) => const Divider(),
                      itemBuilder: (context, index) {
                        final times = ["14:30", "12:15", "10:45", "08:20", "06:00"];
                        final actions = ["OPEN", "CLOSE", "OPEN", "CLOSE", "OPEN"];
                        final reasons = ["Schedule", "Schedule", "Manual", "Schedule", "Schedule"];
                        
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8.0),
                          child: Row(
                            children: [
                              Icon(
                                actions[index] == "OPEN"
                                    ? Icons.arrow_upward
                                    : Icons.arrow_downward,
                                color: actions[index] == "OPEN"
                                    ? Colors.green
                                    : Colors.red,
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      "${actions[index]} - ${reasons[index]}",
                                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                    Text(
                                      "Today at ${times[index]}",
                                      style: Theme.of(context).textTheme.bodySmall,
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
}
