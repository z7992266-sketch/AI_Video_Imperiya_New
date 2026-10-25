import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../data.dart';
import '../theme.dart';
import '../widgets/ui.dart';
import 'app_form_screen.dart';

class AppDetailScreen extends StatefulWidget {
  final String appId;
  const AppDetailScreen({super.key, required this.appId});
  @override
  State<AppDetailScreen> createState() => _AppDetailScreenState();
}

class _AppDetailScreenState extends State<AppDetailScreen> {
  AppStatus? _app;
  List<CheckRow> _checks = [];
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final apps = await Api.apps();
      final app = apps.where((a) => a.id == widget.appId).firstOrNull;
      final checks = app == null ? <CheckRow>[] : await Api.checks(app.id);
      if (!mounted) return;
      setState(() {
        _app = app;
        _checks = checks;
      });
    } catch (e) {
      if (mounted) toast(context, 'Yuklab bo\'lmadi: $e');
    }
  }

  Future<void> _run(Future<void> Function() action, String done) async {
    setState(() => _busy = true);
    try {
      await action();
      await _load();
      if (mounted) toast(context, done);
    } catch (e) {
      if (mounted) toast(context, 'Xato: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<bool> _confirm(String title, String text) async {
    final r = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        backgroundColor: C.card,
        title: Text(title),
        content: Text(text, style: const TextStyle(color: C.muted)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Bekor', style: TextStyle(color: C.muted))),
          TextButton(onPressed: () => Navigator.pop(c, true), child: const Text('Tasdiqlash', style: TextStyle(color: C.gold))),
        ],
      ),
    );
    return r == true;
  }

  @override
  Widget build(BuildContext context) {
    final a = _app;
    return Scaffold(
      appBar: AppBar(
        title: Text(a?.name ?? ''),
        actions: [
          if (a != null)
            IconButton(
              tooltip: 'Tahrirlash',
              icon: const Icon(Icons.edit_outlined),
              onPressed: () async {
                final r = await Navigator.of(context).push<Object?>(MaterialPageRoute(builder: (_) => AppFormScreen(app: a)));
                if (r == 'deleted' && context.mounted) {
                  Navigator.of(context).pop();
                } else {
                  _load();
                }
              },
            ),
        ],
      ),
      body: a == null
          ? const Center(child: CircularProgressIndicator(color: C.gold))
          : RefreshIndicator(
              color: C.gold,
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
                children: [
                  Row(children: [
                    AppBadge(a.initials),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text([if (a.platform.isNotEmpty) a.platform, if (a.version.isNotEmpty) 'v${a.version}'].join(' · '),
                          style: const TextStyle(color: C.muted)),
                    ),
                    HealthDot(a.health),
                  ]),
                  const SizedBox(height: 16),
                  if (a.health == Health.down) ...[
                    CardBox(
                      color: C.badBg,
                      border: C.badLine,
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(a.incidentTitle ?? 'Ilova javob bermayapti', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                        const SizedBox(height: 6),
                        Text('Boshlandi: ${ago(a.incidentStartedAt ?? a.lastCheckedAt)}',
                            style: const TextStyle(color: Color(0xFFF0C4C5), fontSize: 13)),
                        const SizedBox(height: 10),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(color: const Color(0xFF120A0B), borderRadius: BorderRadius.circular(12)),
                          child: Text(
                            '${a.lastError ?? 'Javob yo\'q'}\n${a.healthUrl ?? ''}',
                            style: const TextStyle(fontFamily: 'monospace', fontSize: 12, color: Color(0xFFFFB4B6), height: 1.5),
                          ),
                        ),
                      ]),
                    ),
                    const SizedBox(height: 12),
                    CardBox(
                      border: C.goldDim,
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        const Row(children: [
                          Icon(Icons.auto_awesome, color: C.gold, size: 18),
                          SizedBox(width: 8),
                          Text('Tavsiya', style: TextStyle(color: C.gold, fontWeight: FontWeight.w700)),
                        ]),
                        const SizedBox(height: 8),
                        Text(_advice(a), style: const TextStyle(color: Color(0xFFD9D4C8), height: 1.45)),
                      ]),
                    ),
                    const SizedBox(height: 16),
                  ],
                  const Text('Bitta tugma bilan', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 10),
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    mainAxisSpacing: 10,
                    crossAxisSpacing: 10,
                    childAspectRatio: 2.1,
                    children: [
                      _Action(
                        title: 'Hozir tekshirish',
                        sub: a.healthUrl == null ? 'Avval URL kiriting' : 'Serverga so\'rov',
                        icon: Icons.refresh_rounded,
                        onTap: (_busy || a.healthUrl == null)
                            ? null
                            : () => _run(() => Api.checkNow(a.id), 'Tekshirildi'),
                      ),
                      _Action(
                        title: a.maintenance ? 'Texnik rejimni o\'chirish' : 'Texnik rejim',
                        sub: a.maintenance ? 'Hozir yoqilgan' : 'Mijozlarga xabar',
                        icon: Icons.construction_rounded,
                        highlight: a.maintenance,
                        onTap: _busy
                            ? null
                            : () async {
                                final on = !a.maintenance;
                                if (on && !await _confirm('Texnik rejim', 'Ilova foydalanuvchilariga "${a.maintenanceMessage}" xabari ko\'rsatiladi. Yoqaymi?')) {
                                  return;
                                }
                                await _run(() => Api.setMaintenance(a.id, on), on ? 'Texnik rejim yoqildi' : 'Texnik rejim o\'chirildi');
                              },
                      ),
                      _Action(
                        title: 'Muammoni yopish',
                        sub: 'Qo\'lda hal qilindi',
                        icon: Icons.check_circle_outline,
                        onTap: (_busy || a.incidentId == null)
                            ? null
                            : () => _run(() => Api.resolveIncident(a.incidentId!, a.id), 'Muammo yopildi'),
                      ),
                      const _Action(
                        title: 'Oldingi versiya',
                        sub: 'Tez kunda',
                        icon: Icons.history_rounded,
                        onTap: null,
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  const Text('Oxirgi tekshiruvlar', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 10),
                  if (_checks.isEmpty)
                    Text(
                      a.healthUrl == null
                          ? 'Kuzatish uchun ✎ tugmasini bosib, ilovaning tekshiruv manzilini (URL) kiriting.'
                          : 'Hali tekshiruv yo\'q. Bir daqiqadan keyin paydo bo\'ladi.',
                      style: const TextStyle(color: C.muted),
                    )
                  else ...[
                    _LatencyBars(_checks.reversed.toList()),
                    const SizedBox(height: 12),
                    CardBox(
                      color: const Color(0xFF101012),
                      border: const Color(0xFF1F1F22),
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        children: [
                          for (final c in _checks.take(12))
                            Padding(
                              padding: const EdgeInsets.symmetric(vertical: 3),
                              child: Row(children: [
                                SizedBox(
                                  width: 64,
                                  child: Text(DateFormat('HH:mm:ss').format(c.at),
                                      style: const TextStyle(fontFamily: 'monospace', fontSize: 11, color: C.muted)),
                                ),
                                Text(c.statusCode?.toString() ?? '—',
                                    style: TextStyle(fontFamily: 'monospace', fontSize: 11, color: c.ok ? C.ok : C.bad)),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Text(c.ok ? '${c.latencyMs} ms' : (c.error ?? 'xato'),
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(fontFamily: 'monospace', fontSize: 11, color: C.muted)),
                                ),
                              ]),
                            ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }

  String _advice(AppStatus a) {
    final e = (a.lastError ?? '').toLowerCase();
    if (e.contains('timeout')) {
      return 'Server javob berishga ulgurmayapti. Serverni qayta ishga tushiring yoki yuklama oshganini tekshiring. Mijozlar xavotir olmasligi uchun texnik rejimni yoqing.';
    }
    if (e.contains('http 5')) {
      return 'Server ichida xato (5xx). Ko\'pincha oxirgi yangilanishdan keyin chiqadi — oldingi ishlagan versiyaga qaytaring va loglarni tekshiring.';
    }
    if (e.contains('http 4')) {
      return 'Manzil topilmadi yoki ruxsat yo\'q (4xx). Tekshiruv URL\'i to\'g\'riligini va kalitlar muddati o\'tmaganini tekshiring.';
    }
    if (e.contains('dns') || e.contains('connect') || e.contains('refused')) {
      return 'Serverga umuman ulanib bo\'lmayapti. Hosting, domen va SSL sertifikat muddatini tekshiring.';
    }
    return 'Ilova javob bermayapti. Serverni tekshiring, kerak bo\'lsa texnik rejimni yoqing.';
  }
}

class _Action extends StatelessWidget {
  final String title;
  final String sub;
  final IconData icon;
  final VoidCallback? onTap;
  final bool highlight;
  const _Action({required this.title, required this.sub, required this.icon, this.onTap, this.highlight = false});

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: onTap == null ? 0.45 : 1,
      child: CardBox(
        color: highlight ? C.goldBg : C.card,
        border: highlight ? C.goldDim : C.line,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        onTap: onTap,
        child: Row(children: [
          Icon(icon, color: highlight ? C.gold : C.text, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: highlight ? C.gold : C.text)),
                const SizedBox(height: 2),
                Text(sub, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: C.muted, fontSize: 11)),
              ],
            ),
          ),
        ]),
      ),
    );
  }
}

class _LatencyBars extends StatelessWidget {
  final List<CheckRow> checks;
  const _LatencyBars(this.checks);

  @override
  Widget build(BuildContext context) {
    final maxMs = checks.map((c) => c.latencyMs ?? 0).fold<int>(1, (m, v) => v > m ? v : m);
    return CardBox(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Javob vaqti (ms)', style: TextStyle(color: C.muted, fontSize: 12)),
        const SizedBox(height: 8),
        SizedBox(
          height: 64,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              for (final c in checks)
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 1.5),
                    child: Container(
                      height: c.ok ? (64 * ((c.latencyMs ?? 0) / maxMs)).clamp(4, 64).toDouble() : 64,
                      decoration: BoxDecoration(
                        color: c.ok ? ((c.latencyMs ?? 0) > 2000 ? C.warn : C.ok) : C.bad,
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 6),
        Text('Eng sekin: $maxMs ms', style: const TextStyle(color: C.muted, fontSize: 11)),
      ]),
    );
  }
}
