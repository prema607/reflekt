import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _L();
}

class _L extends State<LoginScreen> {
  final email = TextEditingController(), pass = TextEditingController();
  String? err;
  bool busy = false;

  Future<void> _go(bool create) async {
    setState(() { busy = true; err = null; });
    try {
      final a = FirebaseAuth.instance;
      create
          ? await a.createUserWithEmailAndPassword(email: email.text.trim(), password: pass.text)
          : await a.signInWithEmailAndPassword(email: email.text.trim(), password: pass.text);
    } on FirebaseAuthException catch (e) {
      err = e.message;
    }
    if (mounted) setState(() => busy = false);
  }

  @override
  Widget build(BuildContext c) => Scaffold(
        body: Center(child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 360),
          child: Padding(padding: const EdgeInsets.all(24), child: Column(
            mainAxisSize: MainAxisSize.min, children: [
            const Text('Virtual Try-On', style: TextStyle(fontSize: 26)),
            const SizedBox(height: 16),
            TextField(controller: email, decoration: const InputDecoration(labelText: 'Email')),
            TextField(controller: pass, obscureText: true,
                decoration: const InputDecoration(labelText: 'Password')),
            if (err != null) Padding(padding: const EdgeInsets.all(8),
                child: Text(err!, style: const TextStyle(color: Colors.red))),
            const SizedBox(height: 12),
            FilledButton(onPressed: busy ? null : () => _go(false), child: const Text('Sign in')),
            TextButton(onPressed: busy ? null : () => _go(true), child: const Text('Create account')),
          ])))));
}
