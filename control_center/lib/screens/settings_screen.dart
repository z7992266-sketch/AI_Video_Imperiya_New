import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../security.dart';
import '../theme.dart';
import '../widgets/ui.dart';
import 'lock_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _bioBor = false;

  static const _qulfVariant = [
    Duration(seconds: 30),
    Duration(minutes: 1),
    Duration(minutes: 5),
    Duration(minutes: 15),
    Duration(minutes: 30),
  ];

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    await Security.load();
    final v = await Security.canBiometric();
    if (mounted) setState(() => _bioBor = v);
  }

  String _vaqt(Duration d) => d.inSeconds < 60 ? '${d.inSeconds} soniya' : '${d.inMinutes} daqiqa';

  Future<void> _bioAlmashtir(bool on) async {
    if (on) {
      // Yoqishdan oldin egasi ekanini tasdiqlaymiz.
      final ok = await Security.biometric();
      if (!ok) {
        if (mounted) toast(context, 'Tasdiqlanmadi');
        return;
      }
    }
    await Security.setBio(on);
    if (mounted) {
      setState(() {});
      toast(context, on ? 'Biometrik kirish yoqildi ✅' : 'Biometrik kirish o\'chirildi');
    }
  }

  Future<void> _pinAlmashtir() async {
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (c) => LockScreen(
        change: true,
        onUnlocked: () {
          Navigator.of(c).pop();
          toast(context, 'Yangi PIN saqlandi ✅');
        },
      ),
    ));
  }

  Future<void> _qulfTanla() async {
    final d = await showModalBottomSheet<Duration>(
      context: context,
      backgroundColor: C.card,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(22))),
      builder: (c) => SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Padding(
            padding: EdgeInsets.all(16),
            child: Text('Avtomatik qulf', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
          ),
          for (final v in _qulfVariant)
            ListTile(
              leading: Icon(v == Security.lockAfter ? Icons.radio_button_checked : Icons.radio_button_off, color: C.gold),
              title: Text('Ilova ${_vaqt(v)} yopiq tursa'),
              onTap: () => Navigator.pop(c, v),
            ),
          const SizedBox(height: 8),
        ]),
      ),
    );
    if (d == null) return;
    await Security.setLockAfter(d);
    if (mounted) setState(() {});
  }

  void _akkaunt(String email) {
    showModalBottomSheet(
      context: context,
      backgroundColor: C.card,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(22))),
      builder: (c) => SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const SizedBox(height: 8),
          ListTile(
            leading: const Icon(Icons.copy_rounded, color: C.gold),
            title: const Text('Email\'ni nusxalash'),
            subtitle: Text(email, style: const TextStyle(color: C.muted)),
            onTap: () {
              Clipboard.setData(ClipboardData(text: email));
              Navigator.pop(c);
              toast(context, 'Nusxalandi');
            },
          ),
          ListTile(
            leading: const Icon(Icons.logout_rounded, color: C.bad),
            title: const Text('Akkauntdan chiqish', style: TextStyle(color: C.bad)),
            onTap: () async {
              Navigator.pop(c);
              await _chiqish();
            },
          ),
          const SizedBox(height: 8),
        ]),
      ),
    );
  }

  void _malumot() {
    showDialog(
      context: context,
      builder: (c) => AlertDialog(
        backgroundColor: C.card,
        title: const Text('Ma\'lumotlar xavfsizligi'),
        content: const Text(
          '• Server bilan ulanish shifrlangan (HTTPS).\n'
          '• Bazadagi har bir jadval Row Level Security bilan himoyalangan — faqat egasi (siz) ko\'ra oladi.\n'
          '• PIN-kod telefonda shifrlangan xotirada saqlanadi.\n'
          '• 5 ta xato urinishdan keyin PIN bloklanadi.',
          style: TextStyle(color: C.muted, height: 1.5),
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(c), child: const Text('OK', style: TextStyle(color: C.gold)))],
      ),
    );
  }

  Future<void> _chiqish() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        backgroundColor: C.card,
        title: const Text('Chiqish'),
        content: const Text('Akkauntdan chiqasizmi? Keyingi kirishda email va yangi PIN kerak bo\'ladi.', style: TextStyle(color: C.muted)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Bekor', style: TextStyle(color: C.muted))),
          TextButton(onPressed: () => Navigator.pop(c, true), child: const Text('Chiqish', style: TextStyle(color: C.bad))),
        ],
      ),
    );
    if (ok != true) return;
    await Security.clear();
    await Supabase.instance.client.auth.signOut();
  }

  Widget _row(IconData i, String t, String s, Color c, {VoidCallback? onTap, Widget? trailing}) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: CardBox(
          onTap: onTap,
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
            trailing ?? (onTap != null ? const Icon(Icons.chevron_right, color: C.muted) : const SizedBox()),
          ]),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final email = Supabase.instance.client.auth.currentUser?.email ?? '—';
    final bioYoniq = _bioBor && Security.bioOn;
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
      children: [
        const Text('Xavfsizlik', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
        const SizedBox(height: 16),
        _row(Icons.person_outline, 'Akkaunt', email, C.gold, onTap: () => _akkaunt(email)),
        _row(
          Icons.fingerprint,
          'Biometrik kirish',
          !_bioBor ? 'Bu qurilmada mavjud emas' : (bioYoniq ? 'Yoqilgan (Face ID / barmoq izi)' : 'O\'chirilgan'),
          bioYoniq ? C.ok : C.muted,
          onTap: _bioBor ? () => _bioAlmashtir(!Security.bioOn) : null,
          trailing: _bioBor ? Switch(value: Security.bioOn, activeColor: C.gold, onChanged: _bioAlmashtir) : null,
        ),
        _row(Icons.pin_outlined, 'PIN-kod', '${Security.pinLength} xonali · 5 ta xato urinishdan keyin bloklanadi · bosib almashtiring', C.ok,
            onTap: _pinAlmashtir),
        _row(Icons.timer_outlined, 'Avtomatik qulf', 'Ilova ${_vaqt(Security.lockAfter)} yopiq tursa, qayta qulflanadi', C.ok, onTap: _qulfTanla),
        _row(Icons.lock_outline, 'Ma\'lumotlar', 'Shifrlangan ulanish · faqat egasi ko\'ra oladi (RLS)', C.ok, onTap: _malumot),
        const SizedBox(height: 16),
        GhostButton(label: 'PIN-kodni almashtirish', icon: Icons.password_rounded, onTap: _pinAlmashtir),
        const SizedBox(height: 10),
        GhostButton(label: 'Chiqish', icon: Icons.logout_rounded, color: C.bad, onTap: _chiqish),
        const SizedBox(height: 24),
        const Center(child: Text('Control Center v1.3 · B2B SAS', style: TextStyle(color: C.muted, fontSize: 12))),
      ],
    );
  }
}
