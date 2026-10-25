import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../data.dart';
import '../theme.dart';
import '../widgets/ui.dart';

class IncidentsScreen extends StatefulWidget {
  const IncidentsScreen({super.key});
  @override
  State<IncidentsScreen> createState() => _IncidentsScreenState();
}

class _IncidentsScreenState extends State<IncidentsScreen> {
  List<IncidentRow> _rows = [];
  Map<String, String> _names = {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final rows = await Api.incidents();
      final apps = await Api.apps();
      if (!mounted) return;
      setState(() {
        _rows = rows;
        _names = {for (final a in apps) a.id: a.name};
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _loading = false);
      toast(context, 'Yuklab bo\'lmadi: $e');
    }
  }

  String _duration(IncidentRow r) {
    final end = r.resolvedAt ?? DateTime.now();
    final d = end.difference(r.startedAt);
    if (d.inMinutes < 1) return '${d.inSeconds} s';
    if (d.inHours < 1) return '${d.inMinutes} daq';
    return '${d.inHours} soat ${d.inMinutes % 60} daq';
  }

  @override
  Widget build(BuildContext context) {
    final fmt = DateFormat('dd.MM HH:mm');
    return RefreshIndicator(
      color: C.gold,
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
        children: [
          const Text('Xatolar tarixi', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
          const SizedBox(height: 16),
          if (_loading)
            const Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator(color: C.gold)))
          else if (_rows.isEmpty)
            const CardBox(
              child: Row(children: [
                Icon(Icons.check_circle_outline, color: C.ok),
                SizedBox(width: 12),
                Expanded(child: Text('Hozircha xato bo\'lmagan. Hammasi joyida 👌', style: TextStyle(color: C.muted))),
              ]),
            )
          else
            for (final r in _rows) ...[
              CardBox(
                border: r.resolvedAt == null ? C.badLine : C.line,
                color: r.resolvedAt == null ? C.badBg : C.card,
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Expanded(
                      child: Text(_names[r.appId] ?? r.title, style: const TextStyle(fontWeight: FontWeight.w700)),
                    ),
                    Text(
                      r.resolvedAt == null ? '● Davom etyapti' : '✓ Hal qilindi',
                      style: TextStyle(color: r.resolvedAt == null ? C.bad : C.ok, fontSize: 12, fontWeight: FontWeight.w700),
                    ),
                  ]),
                  const SizedBox(height: 6),
                  Text(r.lastError ?? r.title, style: const TextStyle(color: C.muted, fontSize: 13)),
                  const SizedBox(height: 6),
                  Text('${fmt.format(r.startedAt)} · ${_duration(r)} · ${r.failCount} ta xato tekshiruv',
                      style: const TextStyle(color: C.muted, fontSize: 12)),
                ]),
              ),
              const SizedBox(height: 8),
            ],
        ],
      ),
    );
  }
}
