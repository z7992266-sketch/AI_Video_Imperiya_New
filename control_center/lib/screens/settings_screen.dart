import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../security.dart';
import '../theme.dart';
import '../widgets/ui.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _bio = false;

  @override
  void initState() {
    super.initState();
    Security.canBiometric().then((v) {
      if (mounted) setState(() => _bio = v);
    });
  }

  Future<void> _changePin() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        backgroundColor: C.card,
        title: const Text('PIN-kodni almashtirish'),
        content: const Text('Joriy PIN o\'chiriladi va keyingi kirishda yangisini yaratasiz.', style: TextStyle(color: C.muted)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Bekor', style: TextStyle(color: C.muted))),
          TextButton(onPressed: () => Navigator.pop(c, true), child: const Text('Davom etish', style: TextStyle(color: C.gold))),
        ],
      ),
    );
    if (ok != true) return;
    await Security.clear();
    await Supabase.instance.client.auth.signOut();
  }

  @override
  Widget build(BuildContext context) {
    final user = Supabase.instance.client.auth.currentUser;
    Widget row(IconData i, String t, String s, Color c) => Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: CardBox(
            child: Row(children: [
              Icon(i, color: c),
              const SizedBox(width: 12),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(t, style: const TextStyle(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 2),
                  Text(s, style: const TextStyle(color: C.muted, fontSize: 12)),
                ]),
              ),
            ]),
          ),
        );
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
      children: [
        const Text('Xavfsizlik', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
        const SizedBox(height: 16),
        row(Icons.person_outline, 'Akkaunt', user?.email ?? '—', C.gold),
        row(Icons.fingerprint, 'Biometrik kirish', _bio ? 'Yoqilgan (Face ID / barmoq izi)' : 'Bu qurilmada mavjud emas', _bio ? C.ok : C.muted),
        row(Icons.pin_outlined, 'PIN-kod', '6 xonali · 5 ta xato urinishdan keyin bloklanadi', C.ok),
        row(Icons.timer_outlined, 'Avtomatik qulf', 'Ilova 1 daqiqa yopiq tursa, qayta qulflanadi', C.ok),
        row(Icons.lock_outline, 'Ma\'lumotlar', 'Shifrlangan ulanish · faqat egasi ko\'ra oladi (RLS)', C.ok),
        const SizedBox(height: 16),
        GhostButton(label: 'PIN-kodni almashtirish', icon: Icons.password_rounded, onTap: _changePin),
        const SizedBox(height: 10),
        GhostButton(
          label: 'Chiqish',
          icon: Icons.logout_rounded,
          color: C.bad,
          onTap: () async {
            await Security.clear();
            await Supabase.instance.client.auth.signOut();
          },
        ),
        const SizedBox(height: 24),
        const Center(child: Text('Control Center v1.0.0', style: TextStyle(color: C.muted, fontSize: 12))),
      ],
    );
  }
}
