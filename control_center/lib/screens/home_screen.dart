import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../data.dart';
import '../theme.dart';
import '../widgets/ui.dart';
import 'app_detail_screen.dart';
import 'app_form_screen.dart';
import 'billing_screen.dart';
import 'incidents_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tab = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [const PanelPage(), const IncidentsScreen(), const BillingScreen(), const SettingsScreen()];
    return Scaffold(
      body: SafeArea(child: IndexedStack(index: _tab, children: pages)),
      bottomNavigationBar: NavigationBarTheme(
        data: NavigationBarThemeData(
          backgroundColor: const Color(0xFF0E0E10),
          indicatorColor: C.goldBg,
          labelTextStyle: WidgetStateProperty.resolveWith(
            (s) => TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: s.contains(WidgetState.selected) ? C.gold : C.muted,
            ),
          ),
          iconTheme: WidgetStateProperty.resolveWith(
            (s) => IconThemeData(color: s.contains(WidgetState.selected) ? C.gold : C.muted),
          ),
        ),
        child: NavigationBar(
          selectedIndex: _tab,
          onDestinationSelected: (i) => setState(() => _tab = i),
          destinations: const [
            NavigationDestination(icon: Icon(Icons.grid_view_rounded), label: 'Panel'),
            NavigationDestination(icon: Icon(Icons.warning_amber_rounded), label: 'Xatolar'),
            NavigationDestination(icon: Icon(Icons.credit_card_rounded), label: 'To\'lov'),
            NavigationDestination(icon: Icon(Icons.shield_outlined), label: 'Xavfsizlik'),
          ],
        ),
      ),
    );
  }
}

class PanelPage extends StatefulWidget {
  const PanelPage({super.key});
  @override
  State<PanelPage> createState() => _PanelPageState();
}

class _PanelPageState extends State<PanelPage> {
  List<AppStatus> _apps = [];
  bool _loading = true;
  String? _error;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _load();
    _timer = Timer.periodic(const Duration(seconds: 20), (_) => _load(silent: true));
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent) setState(() => _loading = true);
    try {
      final a = await Api.apps();
      if (!mounted) return;
      setState(() {
        _apps = a;
        _error = null;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Server bilan aloqa yo\'q: $e';
        _loading = false;
      });
    }
  }

  Future<void> _checkAll() async {
    try {
      await Api.checkNow();
      await _load(silent: true);
      if (mounted) toast(context, 'Hammasi tekshirildi');
    } catch (e) {
      if (mounted) toast(context, 'Tekshirib bo\'lmadi: $e');
    }
  }

  Future<void> _open(AppStatus a) async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => AppDetailScreen(appId: a.id)));
    _load(silent: true);
  }

  Future<void> _add() async {
    final saved = await Navigator.of(context).push<bool>(MaterialPageRoute(builder: (_) => const AppFormScreen()));
    if (saved == true) _load();
  }

  @override
  Widget build(BuildContext context) {
    final monitored = _apps.where((a) => a.health != Health.unknown).toList();
    final good = monitored.where((a) => a.health == Health.ok || a.health == Health.slow).length;
    final down = _apps.where((a) => a.health == Health.down).toList();
    DateTime? lastCheck;
    for (final a in _apps) {
      if (a.lastCheckedAt != null && (lastCheck == null || a.lastCheckedAt!.isAfter(lastCheck))) lastCheck = a.lastCheckedAt;
    }
    final latencies = monitored.map((a) => a.lastLatencyMs).whereType<int>().toList();
    final avgLatency = latencies.isEmpty ? null : (latencies.reduce((x, y) => x + y) / latencies.length).round();

    return RefreshIndicator(
      color: C.gold,
      backgroundColor: C.card,
      onRefresh: _checkAll,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
        children: [
          Row(children: [
            const Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('B2B SAS', style: TextStyle(color: C.goldDeep, letterSpacing: 2, fontSize: 12, fontWeight: FontWeight.w700)),
                SizedBox(height: 2),
                Text('Control Center', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
              ]),
            ),
            IconButton.filledTonal(
              style: IconButton.styleFrom(backgroundColor: C.card),
              tooltip: 'Hozir tekshirish',
              onPressed: _checkAll,
              icon: const Icon(Icons.refresh_rounded, color: C.text),
            ),
          ]),
          const SizedBox(height: 16),
          if (_loading && _apps.isEmpty)
            const Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator(color: C.gold)))
          else ...[
            if (_error != null) ...[
              CardBox(color: C.badBg, border: C.badLine, child: Text(_error!, style: const TextStyle(color: Color(0xFFF0C4C5)))),
              const SizedBox(height: 12),
            ],
            _Summary(total: monitored.length, good: good, down: down.length, lastCheck: lastCheck, avgLatency: avgLatency),
            for (final a in down) ...[
              const SizedBox(height: 12),
              CardBox(
                color: C.badBg,
                border: C.badLine,
                onTap: () => _open(a),
                child: Row(children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(color: C.bad, borderRadius: BorderRadius.circular(12)),
                    child: const Icon(Icons.warning_amber_rounded, color: Colors.white),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(a.incidentTitle ?? '${a.name} — xato', style: const TextStyle(fontWeight: FontWeight.w700)),
                      const SizedBox(height: 2),
                      Text('${a.lastError ?? 'Javob yo\'q'} · ${ago(a.incidentStartedAt ?? a.lastCheckedAt)}',
                          style: const TextStyle(color: Color(0xFFF0A9AB), fontSize: 12)),
                    ]),
                  ),
                  const Text('Tuzatish ›', style: TextStyle(color: C.gold, fontWeight: FontWeight.w700)),
                ]),
              ),
            ],
            const SizedBox(height: 20),
            Text('Ilovalar (${_apps.length})', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            for (final a in _apps) ...[
              CardBox(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                border: a.health == Health.down ? C.badLine : C.line,
                onTap: () => _open(a),
                child: Row(children: [
                  AppBadge(a.initials),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(a.name, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                      const SizedBox(height: 2),
                      Text(
                        [
                          if (a.platform.isNotEmpty) a.platform,
                          if (a.version.isNotEmpty) 'v${a.version}',
                          if (a.lastLatencyMs != null) '${a.lastLatencyMs} ms',
                          if (a.healthUrl == null) 'manzil kiritilmagan',
                        ].join(' · '),
                        style: const TextStyle(color: C.muted, fontSize: 12),
                      ),
                    ]),
                  ),
                  HealthDot(a.health),
                ]),
              ),
              const SizedBox(height: 8),
            ],
            const SizedBox(height: 4),
            SizedBox(
              height: 56,
              child: OutlinedButton.icon(
                onPressed: _add,
                style: OutlinedButton.styleFrom(
                  foregroundColor: C.gold,
                  side: const BorderSide(color: C.goldDim, style: BorderStyle.solid),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                icon: const Icon(Icons.add),
                label: const Text('Yangi ilova qo\'shish', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Summary extends StatelessWidget {
  final int total;
  final int good;
  final int down;
  final DateTime? lastCheck;
  final int? avgLatency;
  const _Summary({required this.total, required this.good, required this.down, this.lastCheck, this.avgLatency});

  @override
  Widget build(BuildContext context) {
    final String title;
    if (total == 0) {
      title = 'Kuzatuv sozlanmagan';
    } else if (down == 0) {
      title = 'Umumiy holat: a\'lo';
    } else {
      title = '$down ta ilovada xato';
    }
    return CardBox(
      padding: const EdgeInsets.all(18),
      child: Row(children: [
        SizedBox(
          width: 84,
          height: 84,
          child: CustomPaint(
            painter: _RingPainter(total == 0 ? 0 : good / total),
            child: Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Text('$good/$total', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                const Text('ishlayapti', style: TextStyle(fontSize: 10, color: C.muted)),
              ]),
            ),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            Text(
              total == 0
                  ? 'Ilovaga kirib, tekshiriladigan manzilni (URL) qo\'shing.'
                  : 'Oxirgi tekshiruv: ${ago(lastCheck)}',
              style: const TextStyle(color: C.muted, fontSize: 13),
            ),
            if (avgLatency != null) ...[
              const SizedBox(height: 6),
              Text('● O\'rtacha javob: $avgLatency ms',
                  style: TextStyle(color: avgLatency! > 2000 ? C.warn : C.ok, fontSize: 12, fontWeight: FontWeight.w600)),
            ],
          ]),
        ),
      ]),
    );
  }
}

class _RingPainter extends CustomPainter {
  final double value;
  _RingPainter(this.value);
  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final stroke = size.width * 0.11;
    final r = rect.deflate(stroke / 2);
    final bg = Paint()
      ..color = value == 0 ? C.line : C.bad
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke;
    canvas.drawArc(r, 0, math.pi * 2, false, bg);
    if (value > 0) {
      final fg = Paint()
        ..color = C.ok
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round
        ..strokeWidth = stroke;
      canvas.drawArc(r, -math.pi / 2, math.pi * 2 * value, false, fg);
    }
  }

  @override
  bool shouldRepaint(_RingPainter old) => old.value != value;
}
