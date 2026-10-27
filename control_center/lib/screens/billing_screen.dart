import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../data.dart';
import '../theme.dart';
import '../widgets/ui.dart';

/// Egasining to'lov rekvizitlari: restoranlar obuna to'lovini shu kartaga qiladi.
/// Rekvizit Telegram bot va saytda ko'rsatiladi (Play qoidasi: ilova ichida emas).
/// Faqat karta RAQAMI saqlanadi — CVV va amal qilish muddati hech qachon so'ralmaydi.
class BillingScreen extends StatefulWidget {
  const BillingScreen({super.key});
  @override
  State<BillingScreen> createState() => _BillingScreenState();
}

class _BillingScreenState extends State<BillingScreen> {
  final _card = TextEditingController();
  final _holder = TextEditingController();
  final _bank = TextEditingController();
  final _sbp = TextEditingController();
  final _uzs = TextEditingController();
  final _rub = TextEditingController();
  final _note = TextEditingController();
  bool _active = true;
  bool _loading = true;
  bool _saving = false;
  DateTime? _updated;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in [_card, _holder, _bank, _sbp, _uzs, _rub, _note]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final b = await Api.billing();
      _card.text = _fmtCard(b['card_number'] as String? ?? '');
      _holder.text = b['card_holder'] as String? ?? '';
      _bank.text = b['bank'] as String? ?? '';
      _sbp.text = b['sbp_phone'] as String? ?? '';
      final u = (b['price_month_uzs'] as num?)?.toInt() ?? 0;
      final r = (b['price_month_rub'] as num?)?.toInt() ?? 0;
      _uzs.text = u == 0 ? '' : '$u';
      _rub.text = r == 0 ? '' : '$r';
      _note.text = b['note'] as String? ?? '';
      _active = b['active'] as bool? ?? true;
      final t = b['updated_at'] as String?;
      _updated = t == null ? null : DateTime.parse(t).toLocal();
    } catch (e) {
      _error = 'Yuklab bo\'lmadi. Internetni tekshiring.';
    }
    if (mounted) setState(() => _loading = false);
  }

  static String _digits(String s) => s.replaceAll(RegExp(r'\D'), '');
  static String _fmtCard(String s) {
    final d = _digits(s);
    final b = StringBuffer();
    for (var i = 0; i < d.length; i++) {
      if (i > 0 && i % 4 == 0) b.write(' ');
      b.write(d[i]);
    }
    return b.toString();
  }

  static bool _luhn(String d) {
    var sum = 0;
    var alt = false;
    for (var i = d.length - 1; i >= 0; i--) {
      var n = int.parse(d[i]);
      if (alt) {
        n *= 2;
        if (n > 9) n -= 9;
      }
      sum += n;
      alt = !alt;
    }
    return sum % 10 == 0;
  }

  Future<void> _save() async {
    final d = _digits(_card.text);
    if (d.isNotEmpty && (d.length < 16 || d.length > 19 || !_luhn(d))) {
      toast(context, 'Karta raqami noto\'g\'ri. 16 xonani tekshiring.');
      return;
    }
    if (d.isNotEmpty && _holder.text.trim().isEmpty) {
      toast(context, 'Karta egasining ismini yozing.');
      return;
    }
    setState(() => _saving = true);
    try {
      await Api.saveBilling({
        'card_number': _fmtCard(d),
        'card_holder': _holder.text.trim(),
        'bank': _bank.text.trim(),
        'sbp_phone': _sbp.text.trim(),
        'price_month_uzs': int.tryParse(_digits(_uzs.text)) ?? 0,
        'price_month_rub': int.tryParse(_digits(_rub.text)) ?? 0,
        'note': _note.text.trim(),
        'active': _active,
      });
      await Api.log(null, 'billing_updated');
      if (mounted) toast(context, 'Saqlandi ✅ Endi obuna to\'lovlari shu kartaga keladi.');
      await _load();
    } catch (e) {
      if (mounted) toast(context, 'Saqlanmadi: $e');
    }
    if (mounted) setState(() => _saving = false);
  }

  Widget _field(String label, TextEditingController c,
      {String? hint, TextInputType? type, List<TextInputFormatter>? fmt, int maxLines = 1}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: c,
        keyboardType: type,
        inputFormatters: fmt,
        maxLines: maxLines,
        onChanged: (_) => setState(() {}),
        style: const TextStyle(color: C.text, fontSize: 16),
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          labelStyle: const TextStyle(color: C.muted),
          hintStyle: const TextStyle(color: C.muted),
          filled: true,
          fillColor: C.card,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: C.line)),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: C.line)),
          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: C.gold)),
        ),
      ),
    );
  }

  Widget _preview() {
    final num = _card.text.isEmpty ? '•••• •••• •••• ••••' : _card.text;
    return Container(
      height: 190,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: const LinearGradient(
          colors: [Color(0xFF1C1810), Color(0xFF3A2C10), Color(0xFF0E0D0A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        border: Border.all(color: C.goldDim),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Text('B2B SAS', style: TextStyle(color: C.gold, fontWeight: FontWeight.w900, letterSpacing: 2)),
          const Spacer(),
          Text(_bank.text.isEmpty ? 'BANK' : _bank.text.toUpperCase(),
              style: const TextStyle(color: C.muted, fontSize: 12, fontWeight: FontWeight.w700)),
        ]),
        const Spacer(),
        FittedBox(
          child: Text(num,
              style: const TextStyle(color: C.text, fontSize: 24, fontWeight: FontWeight.w700, letterSpacing: 2)),
        ),
        const SizedBox(height: 10),
        Row(children: [
          Expanded(
            child: Text(_holder.text.isEmpty ? 'KARTA EGASI' : _holder.text.toUpperCase(),
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: C.muted, fontSize: 13, fontWeight: FontWeight.w700)),
          ),
          if (_sbp.text.isNotEmpty)
            Text('СБП ${_sbp.text}', style: const TextStyle(color: C.gold, fontSize: 12, fontWeight: FontWeight.w700)),
        ]),
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator(color: C.gold));
    return RefreshIndicator(
      color: C.gold,
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        children: [
          const Text('To\'lov tizimi', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          const Text(
            'Restoranlar Smart Sistem obunasini shu kartaga to\'laydi. Rekvizit Telegram bot va saytda ko\'rsatiladi.',
            style: TextStyle(color: C.muted, height: 1.4),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            CardBox(color: C.badBg, border: C.badLine, child: Text(_error!, style: const TextStyle(color: C.bad))),
          ],
          const SizedBox(height: 16),
          _preview(),
          const SizedBox(height: 20),
          _field('Karta raqami', _card,
              hint: '8600 1234 5678 9012',
              type: TextInputType.number,
              fmt: [
                FilteringTextInputFormatter.digitsOnly,
                LengthLimitingTextInputFormatter(19),
                TextInputFormatter.withFunction(
                    (o, n) => TextEditingValue(text: _fmtCard(n.text), selection: TextSelection.collapsed(offset: _fmtCard(n.text).length))),
              ]),
          _field('Karta egasi (ism familiya)', _holder, hint: 'ALISHER ATAXANOV'),
          _field('Bank', _bank, hint: 'Kapitalbank / Tinkoff / Sber'),
          _field('SBP telefon raqami (Rossiya, ixtiyoriy)', _sbp,
              hint: '+7 900 000 00 00', type: TextInputType.phone, fmt: [FilteringTextInputFormatter.allow(RegExp(r'[+0-9 ()-]'))]),
          Row(children: [
            Expanded(
                child: _field('Oylik narx (so\'m)', _uzs,
                    type: TextInputType.number, fmt: [FilteringTextInputFormatter.digitsOnly])),
            const SizedBox(width: 12),
            Expanded(
                child: _field('Oylik narx (₽)', _rub,
                    type: TextInputType.number, fmt: [FilteringTextInputFormatter.digitsOnly])),
          ]),
          _field('Izoh (to\'lov maqsadi)', _note, hint: 'Masalan: restoran nomi va oy', maxLines: 2),
          CardBox(
            child: Row(children: [
              const Icon(Icons.campaign_outlined, color: C.gold),
              const SizedBox(width: 12),
              const Expanded(
                child: Text('Rekvizitni restoranlarga ko\'rsatish', style: TextStyle(fontWeight: FontWeight.w700)),
              ),
              Switch(value: _active, activeColor: C.gold, onChanged: (v) => setState(() => _active = v)),
            ]),
          ),
          const SizedBox(height: 10),
          const CardBox(
            child: Row(children: [
              Icon(Icons.lock_outline, color: C.ok),
              SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Faqat karta raqami saqlanadi. CVV kod va amal qilish muddati hech qachon so\'ralmaydi va saqlanmaydi.',
                  style: TextStyle(color: C.muted, fontSize: 12, height: 1.4),
                ),
              ),
            ]),
          ),
          const SizedBox(height: 18),
          GoldButton(label: 'Saqlash', icon: Icons.check_rounded, busy: _saving, onTap: _save),
          if (_updated != null) ...[
            const SizedBox(height: 10),
            Center(child: Text('Oxirgi o\'zgarish: ${ago(_updated)}', style: const TextStyle(color: C.muted, fontSize: 12))),
          ],
        ],
      ),
    );
  }
}
