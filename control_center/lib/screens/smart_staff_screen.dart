// Smart Sistem restoranlari: direktor / xodim loginlarini berish, tahrirlash va o'chirish.
// Server: Supabase edge function `smart-staff` (Firebase admin). Faqat egasi (is_owner) uchun.
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../data.dart';
import '../theme.dart';
import '../widgets/ui.dart';

const _rollar = ['direktor', 'admin', 'ofitsant', 'oshpaz', 'kuryer'];
const _rolNomi = {
  'direktor': 'Direktor',
  'admin': 'Admin',
  'ofitsant': 'Ofitsant',
  'oshpaz': 'Oshpaz',
  'kuryer': 'Kuryer',
};
const _rolIcon = {
  'direktor': Icons.workspace_premium,
  'admin': Icons.admin_panel_settings,
  'ofitsant': Icons.room_service,
  'oshpaz': Icons.restaurant,
  'kuryer': Icons.delivery_dining,
};

String _yangiParol() {
  const h = 'abcdefghjkmnpqrstuvwxyz';
  const r = '23456789';
  final rnd = Random.secure();
  final s = List.generate(6, (_) => h[rnd.nextInt(h.length)]).join() + List.generate(3, (_) => r[rnd.nextInt(r.length)]).join();
  return s[0].toUpperCase() + s.substring(1);
}

InputDecoration _inp(String label, IconData icon, {Widget? suffix}) => InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon, color: C.gold),
      suffixIcon: suffix,
      filled: true,
      fillColor: C.card,
      labelStyle: const TextStyle(color: C.muted),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: C.line)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: C.line)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: C.gold)),
    );

class SmartStaffScreen extends StatefulWidget {
  const SmartStaffScreen({super.key});
  @override
  State<SmartStaffScreen> createState() => _SmartStaffScreenState();
}

class _SmartStaffScreenState extends State<SmartStaffScreen> {
  List<Map<String, dynamic>>? _rs;
  String? _err;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final r = await Api.smartRestoranlar();
      if (mounted) setState(() {
        _rs = r;
        _err = null;
      });
    } catch (e) {
      if (mounted) setState(() => _err = '$e');
    }
  }

  Future<void> _form({Map<String, dynamic>? x, String? restoranId}) async {
    final ok = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: C.bg,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => _StaffForm(restoranlar: _rs ?? const [], x: x, restoranId: restoranId),
    );
    if (ok == true) _load();
  }

  Future<void> _ochir(Map<String, dynamic> x) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        backgroundColor: C.card,
        title: const Text("Loginni o'chirish"),
        content: Text("${x['name']} (${x['login']})\n\nLogin butunlay o'chiriladi va u ilovaga kira olmaydi.",
            style: const TextStyle(color: C.muted)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Bekor', style: TextStyle(color: C.muted))),
          TextButton(onPressed: () => Navigator.pop(c, true), child: const Text("O'chirish", style: TextStyle(color: C.bad))),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await Api.smartStaff({'op': 'delete', 'uid': x['uid']});
      if (mounted) toast(context, "O'chirildi ✅");
      _load();
    } catch (e) {
      if (mounted) toast(context, '$e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final rs = _rs;
    return Scaffold(
      appBar: AppBar(title: const Text('Loginlar (Smart Sistem)')),
      floatingActionButton: rs == null || rs.isEmpty
          ? null
          : FloatingActionButton.extended(
              backgroundColor: C.gold,
              foregroundColor: C.bg,
              icon: const Icon(Icons.person_add_alt_1),
              label: const Text('Login berish', style: TextStyle(fontWeight: FontWeight.w800)),
              onPressed: () => _form(),
            ),
      body: _err != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(_err!, textAlign: TextAlign.center, style: const TextStyle(color: C.bad)),
                  const SizedBox(height: 12),
                  GhostButton(label: 'Qayta urinish', icon: Icons.refresh, onTap: _load),
                ]),
              ),
            )
          : rs == null
              ? const Center(child: CircularProgressIndicator(color: C.gold))
              : RefreshIndicator(
                  color: C.gold,
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                    children: [
                      if (rs.isEmpty)
                        const Padding(
                          padding: EdgeInsets.all(24),
                          child: Text("Hali restoran yo'q. Avval Smart Admin → Superadmin'da restoran yarating.",
                              textAlign: TextAlign.center, style: TextStyle(color: C.muted)),
                        ),
                      for (final r in rs) ...[
                        _RestoranKarta(
                          r: r,
                          onAdd: () => _form(restoranId: r['id'] as String),
                          onEdit: (x) => _form(x: {...x, 'restoranId': r['id']}),
                          onDelete: _ochir,
                        ),
                        const SizedBox(height: 12),
                      ],
                    ],
                  ),
                ),
    );
  }
}

class _RestoranKarta extends StatelessWidget {
  const _RestoranKarta({required this.r, required this.onAdd, required this.onEdit, required this.onDelete});
  final Map<String, dynamic> r;
  final VoidCallback onAdd;
  final void Function(Map<String, dynamic>) onEdit;
  final void Function(Map<String, dynamic>) onDelete;

  @override
  Widget build(BuildContext context) {
    final staff = ((r['staff'] as List?) ?? const []).cast<Map<String, dynamic>>();
    final faol = r['active'] == true;
    return CardBox(
      padding: const EdgeInsets.all(14),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Icon(Icons.storefront, color: C.gold),
          const SizedBox(width: 10),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('${r['name']}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
              Text([if ((r['phone'] ?? '').toString().isNotEmpty) r['phone'], faol ? 'faol' : "o'chirilgan"].join(' · '),
                  style: TextStyle(color: faol ? C.muted : C.bad, fontSize: 12)),
            ]),
          ),
          IconButton(tooltip: 'Login berish', onPressed: onAdd, icon: const Icon(Icons.person_add_alt_1, color: C.gold)),
        ]),
        const Divider(color: C.line, height: 18),
        if (staff.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 6),
            child: Text("Login berilmagan — ➕ ni bosing", style: TextStyle(color: C.muted, fontSize: 13)),
          ),
        for (final x in staff)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: C.goldBg,
                child: Icon(_rolIcon[x['role']] ?? Icons.person, color: C.gold, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('${x['name']}'.isEmpty ? '${x['login']}' : '${x['name']}',
                      maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w700)),
                  Text('${_rolNomi[x['role']] ?? x['role']} · ${x['login']}${x['active'] == false ? ' · bloklangan' : ''}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: x['active'] == false ? C.bad : C.muted, fontSize: 12)),
                ]),
              ),
              IconButton(
                tooltip: 'Tahrirlash',
                visualDensity: VisualDensity.compact,
                onPressed: () => onEdit(x),
                icon: const Icon(Icons.edit_outlined, color: C.gold, size: 20),
              ),
              IconButton(
                tooltip: "O'chirish",
                visualDensity: VisualDensity.compact,
                onPressed: () => onDelete(x),
                icon: const Icon(Icons.delete_outline, color: C.bad, size: 20),
              ),
            ]),
          ),
      ]),
    );
  }
}

class _StaffForm extends StatefulWidget {
  const _StaffForm({required this.restoranlar, this.x, this.restoranId});
  final List<Map<String, dynamic>> restoranlar;
  final Map<String, dynamic>? x;
  final String? restoranId;
  @override
  State<_StaffForm> createState() => _StaffFormState();
}

class _StaffFormState extends State<_StaffForm> {
  bool get _edit => widget.x != null;
  late String? _rid = widget.x?['restoranId'] as String? ??
      widget.restoranId ??
      (widget.restoranlar.isNotEmpty ? widget.restoranlar.first['id'] as String : null);
  late String _rol = (widget.x?['role'] as String?) ?? 'direktor';
  late final _ism = TextEditingController(text: (widget.x?['name'] as String?) ?? '');
  late final _login = TextEditingController(text: (widget.x?['login'] as String?) ?? '');
  late final _parol = TextEditingController(text: _edit ? '' : _yangiParol());
  late final _tel = TextEditingController(text: (widget.x?['phone'] as String?) ?? '');
  late bool _faol = widget.x?['active'] != false;
  bool _busy = false;

  Future<void> _saqla() async {
    final login = _login.text.trim().toLowerCase();
    setState(() => _busy = true);
    try {
      if (_edit) {
        await Api.smartStaff({
          'op': 'update',
          'uid': widget.x!['uid'],
          'name': _ism.text.trim(),
          if (login != widget.x!['login']) 'login': login,
          if (_parol.text.isNotEmpty) 'password': _parol.text,
          'phone': _tel.text.trim(),
          'role': _rol,
          'active': _faol,
        });
      } else {
        await Api.smartStaff({
          'op': 'create',
          'restoranId': _rid,
          'role': _rol,
          'name': _ism.text.trim(),
          'login': login,
          'password': _parol.text,
          'phone': _tel.text.trim(),
        });
      }
      if (!mounted) return;
      final parol = _parol.text;
      final restoran = widget.restoranlar.where((r) => r['id'] == _rid).map((r) => r['name']).firstOrNull ?? '';
      if (!_edit || parol.isNotEmpty || login != widget.x!['login']) {
        final matn = 'Smart Admin — $restoran\n${_rolNomi[_rol]}: ${_ism.text.trim()}\nLogin: $login${parol.isNotEmpty ? '\nParol: $parol' : ''}';
        await showDialog(
          context: context,
          builder: (c) => AlertDialog(
            backgroundColor: C.card,
            title: Text(_edit ? 'Saqlandi ✅' : 'Login yaratildi ✅'),
            content: SelectableText(matn, style: const TextStyle(height: 1.5)),
            actions: [
              TextButton(
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: matn));
                  toast(c, 'Nusxalandi');
                },
                child: const Text('Nusxalash', style: TextStyle(color: C.gold)),
              ),
              TextButton(onPressed: () => Navigator.pop(c), child: const Text('OK', style: TextStyle(color: C.gold))),
            ],
          ),
        );
      }
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) toast(context, '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + MediaQuery.of(context).viewInsets.bottom),
      child: SingleChildScrollView(
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(_edit ? 'Loginni tahrirlash' : 'Yangi login', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          const SizedBox(height: 16),
          if (!_edit) ...[
            DropdownButtonFormField<String>(
              value: _rid,
              dropdownColor: C.card,
              decoration: _inp('Restoran', Icons.storefront),
              items: [
                for (final r in widget.restoranlar)
                  DropdownMenuItem(value: r['id'] as String, child: Text('${r['name']}')),
              ],
              onChanged: (v) => setState(() => _rid = v),
            ),
            const SizedBox(height: 12),
          ],
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final r in _rollar)
              ChoiceChip(
                label: Text(_rolNomi[r]!, style: TextStyle(color: _rol == r ? C.bg : C.text, fontWeight: FontWeight.w700)),
                selected: _rol == r,
                selectedColor: C.gold,
                backgroundColor: C.card,
                onSelected: (_) => setState(() => _rol = r),
              ),
          ]),
          const SizedBox(height: 12),
          TextField(controller: _ism, decoration: _inp('Ism familiya', Icons.badge_outlined)),
          const SizedBox(height: 12),
          TextField(controller: _login, autocorrect: false, decoration: _inp('Login (masalan: karavan_direktor)', Icons.person_outline)),
          const SizedBox(height: 12),
          TextField(
            controller: _parol,
            decoration: _inp(_edit ? "Yangi parol (bo'sh = o'zgarmaydi)" : 'Parol (kamida 8, harf + raqam)', Icons.lock_outline,
                suffix: IconButton(
                  tooltip: 'Parol yaratish',
                  icon: const Icon(Icons.casino_outlined, color: C.muted),
                  onPressed: () => setState(() => _parol.text = _yangiParol()),
                )),
          ),
          const SizedBox(height: 12),
          TextField(controller: _tel, keyboardType: TextInputType.phone, decoration: _inp('Telefon (ixtiyoriy)', Icons.phone)),
          if (_edit) ...[
            const SizedBox(height: 6),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              activeColor: C.gold,
              title: const Text('Faol (kira oladi)'),
              value: _faol,
              onChanged: (v) => setState(() => _faol = v),
            ),
          ],
          const SizedBox(height: 16),
          GoldButton(label: _edit ? 'Saqlash' : 'Login yaratish', busy: _busy, onTap: _rid == null ? null : _saqla),
        ]),
      ),
    );
  }
}
