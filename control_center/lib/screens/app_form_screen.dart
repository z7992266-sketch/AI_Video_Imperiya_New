import 'package:flutter/material.dart';

import '../data.dart';
import '../theme.dart';
import '../widgets/ui.dart';

/// Add or edit an app. Pops `true` after save, `'deleted'` after delete.
class AppFormScreen extends StatefulWidget {
  final AppStatus? app;
  const AppFormScreen({super.key, this.app});
  @override
  State<AppFormScreen> createState() => _AppFormScreenState();
}

class _AppFormScreenState extends State<AppFormScreen> {
  late final _name = TextEditingController(text: widget.app?.name ?? '');
  late final _short = TextEditingController(text: widget.app?.short ?? '');
  late final _platform = TextEditingController(text: widget.app?.platform ?? '');
  late final _version = TextEditingController(text: widget.app?.version ?? '');
  late final _url = TextEditingController(text: widget.app?.healthUrl ?? '');
  bool _busy = false;

  Future<void> _save() async {
    final name = _name.text.trim();
    final url = _url.text.trim();
    if (name.isEmpty) {
      toast(context, 'Ilova nomini kiriting');
      return;
    }
    if (url.isNotEmpty && !(url.startsWith('https://') || url.startsWith('http://'))) {
      toast(context, 'URL https:// bilan boshlansin');
      return;
    }
    setState(() => _busy = true);
    try {
      await Api.saveApp(
        id: widget.app?.id,
        name: name,
        short: _short.text.trim().toUpperCase(),
        platform: _platform.text.trim(),
        version: _version.text.trim(),
        healthUrl: url,
      );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) toast(context, 'Saqlab bo\'lmadi: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _delete() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        backgroundColor: C.card,
        title: const Text('O\'chirish'),
        content: Text('"${widget.app!.name}" va uning tarixi o\'chiriladi. Ilovaning o\'ziga ta\'sir qilmaydi.',
            style: const TextStyle(color: C.muted)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Bekor', style: TextStyle(color: C.muted))),
          TextButton(onPressed: () => Navigator.pop(c, true), child: const Text('O\'chirish', style: TextStyle(color: C.bad))),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await Api.deleteApp(widget.app!.id);
      if (mounted) Navigator.pop(context, 'deleted');
    } catch (e) {
      if (mounted) toast(context, 'Xato: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final editing = widget.app != null;
    return Scaffold(
      appBar: AppBar(title: Text(editing ? 'Tahrirlash' : 'Yangi ilova')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          TextField(controller: _name, decoration: const InputDecoration(labelText: 'Nomi *', hintText: 'Smart Admin')),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
              child: TextField(
                controller: _short,
                maxLength: 3,
                decoration: const InputDecoration(labelText: 'Belgi', hintText: 'SA', counterText: ''),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              flex: 2,
              child: TextField(controller: _version, decoration: const InputDecoration(labelText: 'Versiya', hintText: '1.0.0')),
            ),
          ]),
          const SizedBox(height: 12),
          TextField(controller: _platform, decoration: const InputDecoration(labelText: 'Platforma', hintText: 'Android · iOS / Web / Bot')),
          const SizedBox(height: 12),
          TextField(
            controller: _url,
            keyboardType: TextInputType.url,
            decoration: const InputDecoration(labelText: 'Tekshiruv manzili (URL)', hintText: 'https://api.misol.uz/health'),
          ),
          const SizedBox(height: 8),
          const Text(
            'Har daqiqada shu manzilga so\'rov yuboriladi. 200 javob — ishlayapti. Ketma-ket 2 marta xato bo\'lsa, signal beriladi.',
            style: TextStyle(color: C.muted, fontSize: 12, height: 1.4),
          ),
          const SizedBox(height: 24),
          GoldButton(label: 'Saqlash', busy: _busy, onTap: _save),
          if (editing) ...[
            const SizedBox(height: 12),
            GhostButton(label: 'Kuzatuvdan o\'chirish', color: C.bad, icon: Icons.delete_outline, onTap: _delete),
          ],
        ],
      ),
    );
  }
}
