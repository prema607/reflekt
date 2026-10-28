import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'firebase/firebase_options.dart';
import 'screens/live_vto_screen.dart';
import 'screens/login_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (DefaultFirebaseOptions.configured) {
    await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  }
  runApp(MaterialApp(
    title: 'VTO', debugShowCheckedModeBanner: false,
    theme: ThemeData(colorSchemeSeed: Colors.pink, useMaterial3: true),
    // Until Firebase keys are filled in, skip login (backend AUTH_REQUIRED=false).
    home: !DefaultFirebaseOptions.configured
        ? const LiveVtoScreen()
        : StreamBuilder<User?>(
            stream: FirebaseAuth.instance.idTokenChanges(),
            builder: (_, s) => s.data == null ? const LoginScreen() : const LiveVtoScreen()),
  ));
}
