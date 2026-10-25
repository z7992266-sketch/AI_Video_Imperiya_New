import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../theme.dart';
import '../widgets/ui.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});
  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _email = TextEditingController();
  final _pass = TextEditingController();
  bool _signUp = false;
  bool _busy = false;
  bool _hide = true;

  Future<void> _submit() async {
    final email = _email.text.trim();
    final pass = _pass.text;
    if (!email.contains('@') || pass.length < 8) {
      toast(context, 'Email to\'g\'ri va parol kamida 8 belgi bo\'lsin');
      return;
    }
    setState(() => _busy = true);
    final auth = Supabase.instance.client.auth;
    try {
      if (_signUp) {
        final r = await auth.signUp(email: email, password: pass);
        if (r.session == null && mounted) {
          toast(context, 'Emailingizga tasdiqlash xati yuborildi. Tasdiqlab, keyin kiring.');
          setState(() => _signUp = false);
        }
      } else {
        await auth.signInWithPassword(email: email, password: pass);
      }
    } on AuthException catch (e) {
      if (mounted) toast(context, e.message);
    } catch (e) {
      if (mounted) toast(context, 'Xato: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(0, -1.1),
            radius: 1.2,
            colors: [Color(0xFF2A2112), C.bg],
          ),
        ),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(24, 56, 24, 24),
            children: [
              const _Logo(),
              const SizedBox(height: 40),
              TextField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.email],
                decoration: const InputDecoration(labelText: 'Email'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _pass,
                obscureText: _hide,
                autofillHints: const [AutofillHints.password],
                decoration: InputDecoration(
                  labelText: 'Parol',
                  suffixIcon: IconButton(
                    icon: Icon(_hide ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: C.muted),
                    onPressed: () => setState(() => _hide = !_hide),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              GoldButton(label: _signUp ? 'Ro\'yxatdan o\'tish' : 'Kirish', busy: _busy, onTap: _submit),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => setState(() => _signUp = !_signUp),
                child: Text(
                  _signUp ? 'Akkaunt bormi? Kirish' : 'Birinchi marta? Akkaunt yaratish',
                  style: const TextStyle(color: C.gold),
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'Faqat egasi kira oladi · Shifrlangan ulanish · Biometrik himoya',
                textAlign: TextAlign.center,
                style: TextStyle(color: C.muted, fontSize: 12),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Logo extends StatelessWidget {
  const _Logo();
  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Container(
        width: 76,
        height: 76,
        decoration: BoxDecoration(
          gradient: C.goldGradient,
          borderRadius: BorderRadius.circular(24),
          boxShadow: [BoxShadow(color: C.gold.withValues(alpha: 0.3), blurRadius: 40, offset: const Offset(0, 12))],
        ),
        child: const Icon(Icons.verified_user_outlined, color: C.bg, size: 38),
      ),
      const SizedBox(height: 18),
      const Text('B2B SAS', style: TextStyle(color: C.goldDeep, letterSpacing: 2.4, fontSize: 12, fontWeight: FontWeight.w700)),
      const SizedBox(height: 6),
      const Text('Control Center', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
      const SizedBox(height: 8),
      const Text('Barcha ilovalaringiz bitta joyda.', style: TextStyle(color: C.muted)),
    ]);
  }
}
