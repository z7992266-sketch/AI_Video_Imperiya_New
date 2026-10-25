import 'package:flutter/material.dart';
import '../data.dart';
import '../theme.dart';

class GoldButton extends StatelessWidget {
  final String label;
  final VoidCallback? onTap;
  final bool busy;
  final IconData? icon;
  const GoldButton({super.key, required this.label, this.onTap, this.busy = false, this.icon});

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: onTap == null ? 0.5 : 1,
      child: Container(
        height: 52,
        decoration: BoxDecoration(gradient: C.goldGradient, borderRadius: BorderRadius.circular(16)),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(16),
            onTap: busy ? null : onTap,
            child: Center(
              child: busy
                  ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.4, color: C.bg))
                  : Row(mainAxisSize: MainAxisSize.min, children: [
                      if (icon != null) ...[Icon(icon, color: C.bg, size: 20), const SizedBox(width: 8)],
                      Text(label, style: const TextStyle(color: C.bg, fontSize: 15, fontWeight: FontWeight.w800)),
                    ]),
            ),
          ),
        ),
      ),
    );
  }
}

class GhostButton extends StatelessWidget {
  final String label;
  final VoidCallback? onTap;
  final IconData? icon;
  final Color color;
  const GhostButton({super.key, required this.label, this.onTap, this.icon, this.color = C.text});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 52,
      child: OutlinedButton(
        onPressed: onTap,
        style: OutlinedButton.styleFrom(
          foregroundColor: color,
          side: const BorderSide(color: C.line),
          backgroundColor: C.card,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          if (icon != null) ...[Icon(icon, size: 20), const SizedBox(width: 8)],
          Text(label, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
        ]),
      ),
    );
  }
}

class CardBox extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  final Color color;
  final Color border;
  final VoidCallback? onTap;
  const CardBox({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.color = C.card,
    this.border = C.line,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18), side: BorderSide(color: border)),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}

class AppBadge extends StatelessWidget {
  final String text;
  const AppBadge(this.text, {super.key});
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 40,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: C.goldBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: C.goldDim),
      ),
      child: Text(text, style: const TextStyle(color: C.gold, fontWeight: FontWeight.w800, fontSize: 13)),
    );
  }
}

Color healthColor(Health h) => switch (h) {
      Health.ok => C.ok,
      Health.slow => C.warn,
      Health.down => C.bad,
      Health.maintenance => C.gold,
      Health.unknown => C.muted,
    };

String healthLabel(Health h) => switch (h) {
      Health.ok => 'Ishlayapti',
      Health.slow => 'Sekin',
      Health.down => 'Xato',
      Health.maintenance => 'Texnik rejim',
      Health.unknown => 'Tekshirilmagan',
    };

class HealthDot extends StatelessWidget {
  final Health health;
  const HealthDot(this.health, {super.key});
  @override
  Widget build(BuildContext context) {
    final c = healthColor(health);
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Container(width: 8, height: 8, decoration: BoxDecoration(color: c, shape: BoxShape.circle)),
      const SizedBox(width: 6),
      Text(healthLabel(health), style: TextStyle(color: c, fontSize: 12, fontWeight: FontWeight.w700)),
    ]);
  }
}

String ago(DateTime? t) {
  if (t == null) return '—';
  final d = DateTime.now().difference(t);
  if (d.inSeconds < 60) return '${d.inSeconds < 0 ? 0 : d.inSeconds} soniya oldin';
  if (d.inMinutes < 60) return '${d.inMinutes} daqiqa oldin';
  if (d.inHours < 24) return '${d.inHours} soat oldin';
  return '${d.inDays} kun oldin';
}

void toast(BuildContext context, String msg) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
}
