import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  static final FlutterLocalNotificationsPlugin _flutterLocalNotificationsPlugin =
      FlutterLocalNotificationsPlugin();

  factory NotificationService() {
    return _instance;
  }

  NotificationService._internal();

  Future<void> initialize() async {
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const DarwinInitializationSettings initializationSettingsIOS =
        DarwinInitializationSettings(
          requestAlertPermission: true,
          requestBadgePermission: true,
          requestSoundPermission: true,
        );

    const InitializationSettings initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid,
      iOS: initializationSettingsIOS,
    );

    await _flutterLocalNotificationsPlugin.initialize(initializationSettings);
    
    // ask ios for permission to nag the user
    await _flutterLocalNotificationsPlugin
        .resolvePlatformSpecificImplementation<
            IOSFlutterLocalNotificationsPlugin>()
        ?.requestPermissions(
          alert: true,
          badge: true,
          sound: true,
        );
    
    // android permissions are declared in AndroidManifest.xml
    // no runtime request needed here
  }

  Future<void> showNotification({
    required String title,
    required String body,
    String? payload,
  }) async {
    const AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
      'door_motor_channel',
      'Door Motor Events',
      channelDescription: 'Notifications for door open/close events',
      importance: Importance.max,
      priority: Priority.high,
      showWhen: true,
    );

    const DarwinNotificationDetails iOSPlatformChannelSpecifics =
        DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        );

    const NotificationDetails platformChannelSpecifics = NotificationDetails(
      android: androidPlatformChannelSpecifics,
      iOS: iOSPlatformChannelSpecifics,
    );

    await _flutterLocalNotificationsPlugin.show(
      0,
      title,
      body,
      platformChannelSpecifics,
      payload: payload,
    );
  }

  Future<void> showDoorOpenNotification() async {
    await showNotification(
      title: 'Door Opened',
      body: 'The door has been opened',
      payload: 'door_open',
    );
  }

  Future<void> showDoorCloseNotification() async {
    await showNotification(
      title: 'Door Closed',
      body: 'The door has been closed',
      payload: 'door_close',
    );
  }

  Future<void> showUnexpectedStateNotification(String state) async {
    await showNotification(
      title: 'Unexpected State',
      body: 'Door is in unexpected state: $state',
      payload: 'unexpected_state',
    );
  }

  Future<void> showBatteryWarningNotification() async {
    await showNotification(
      title: 'Low Battery',
      body: 'Door motor battery is running low',
      payload: 'low_battery',
    );
  }
}
