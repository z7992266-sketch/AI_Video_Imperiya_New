import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../security.dart';
import '../theme.dart';

/// Biometric unlock with a 4-digit PIN fallback. [change] = PIN almashtirish rejimi (eski -> yangi -> tasdiq).
/// On first run it asks the owner to create the PIN (entered twice).
class LockScreen extends StatefulWidget {
  final VoidCallback onUnlocked;
  final bool change;
  const LockScreen({super.key, required this.onUnlocked, this.change = false});
  @override
  State<LockScreen> createState() => _LockScreenState();
}

enum _Mode { loading, create, confirm, enter }

class _LockScreenState extends State<LockScreen> {
  _Mode _mode = _Mode.loading;
  String _pin = '';
  String _first = '';
  bool _bio = false;
  String? _msg;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    await Security.load();
    final has = await Security.hasPin();
    final bio = Security.bioOn && await Security.canBiometric();
    if (!mounted) return;
    setState(() {
      _bio = bio;
      _mode = has ? _Mode.enter : _Mode.create;
    });
    if (has && bio && !widget.change) _tryBio();
  }

  Future<void> _tryBio() async {
    final ok = await Security.biometric();
    if (!ok || !mounted) return;
    if (widget.change) {
      setState(() {
        _pin = '';
        _mode = _Mode.create;
      });
    } else {
      widget.onUnlocked();
    }
  }

  Future<void> _digit(String d) async {
    if (_pin.length >= Security.pinLength) return;
    HapticFeedback.selectionClick();
    setState(() {
      _pin += d;
      _msg = null;
    });
    if (_pin.length < Security.pinLength) return;
    switch (_mode) {
      case _Mode.create:
        setState(() {
          _first = _pin;
          _pin = '';
          _mode = _Mode.confirm;
        });
      case _Mode.confirm:
        if (_pin == _first) {
          await Security.setPin(_pin);
          widget.onUnlocked();
        } else {
          setState(() {
            _pin = '';
            _first = '';
            _mode = _Mode.create;
            _msg = 'PIN mos kelmadi. Qaytadan kiriting.';
          });
        }
      case _Mode.enter:
        final wait = await Security.lockedSeconds();
        if (wait > 0) {
          setState(() {
            _pin = '';
            _msg = 'Juda ko\'p urinish. $wait soniya kuting.';
          });
          return;
        }
        final ok = await Security.checkPin(_pin);
        if (ok && widget.change) {
          setState(() {
            _pin = '';
            _mode = _Mode.create;
          });
        } else if (ok) {
          widget.onUnlocked();
        } else {
          HapticFeedback.heavyImpact();
          final w = await Security.lockedSeconds();
          setState(() {
            _pin = '';
            _msg = w > 0 ? 'Juda ko\'p urinish. $w soniya kuting.' : 'PIN noto\'g\'ri';
          });
        }
      case _Mode.loading:
        break;
    }
  }

  void _back() {
    if (_pin.isEmpty) return;
    setState(() => _pin = _pin.substring(0, _pin.length - 1));
  }

  Future<void> _signOut() async {
    await Security.clear();
    await Supabase.instance.client.auth.signOut();
  }

  String get _title => switch (_mode) {
        _Mode.create => 'Yangi 4 xonali PIN yarating',
        _Mode.confirm => 'PIN\'ni yana bir marta kiriting',
        _Mode.enter => widget.change ? 'Joriy PIN-kodni kiriting' : 'PIN-kodni kiriting',
        _Mode.loading => '',
      };

  @override
  Widget build(BuildContext context) {
    if (_mode == _Mode.loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator(color: C.gold)));
    }
    return Scaffold(
      appBar: widget.change ? AppBar(title: const Text('PIN-kodni almashtirish')) : null,
      body: SafeArea(
        child: Column(
          children: [
            SizedBox(height: widget.change ? 12 : 48),
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(gradient: C.goldGradient, borderRadius: BorderRadius.circular(20)),
              child: const Icon(Icons.lock_outline, color: C.bg, size: 30),
            ),
            const SizedBox(height: 20),
            Text(_title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(Security.pinLength, (i) {
                final filled = i < _pin.length;
                return AnimatedContainer(
                  duration: const Duration(milliseconds: 120),
                  margin: const EdgeInsets.symmetric(horizontal: 8),
                  width: 14,
                  height: 14,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: filled ? C.gold : Colors.transparent,
                    border: Border.all(color: filled ? C.gold : C.line, width: 2),
                  ),
                );
              }),
            ),
            SizedBox(
              height: 36,
              child: Center(
                child: Text(_msg ?? '', style: const TextStyle(color: C.bad, fontSize: 13)),
              ),
            ),
            const Spacer(),
            _Keypad(
              onDigit: _digit,
              onBack: _back,
              leading: (_mode == _Mode.enter && _bio)
                  ? IconButton(
                      iconSize: 30,
                      color: C.gold,
                      icon: const Icon(Icons.fingerprint),
                      tooltip: 'Barmoq izi / Face ID',
                      onPressed: _tryBio,
                    )
                  : null,
            ),
            const SizedBox(height: 12),
            if (widget.change)
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Bekor qilish', style: TextStyle(color: C.muted)),
              )
            else if (_mode == _Mode.enter)
              TextButton(
                onPressed: _signOut,
                child: const Text('PIN esdan chiqdimi? Qayta kirish', style: TextStyle(color: C.muted)),
              ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _Keypad extends StatelessWidget {
  final void Function(String) onDigit;
  final VoidCallback onBack;
  final Widget? leading;
  const _Keypad({required this.onDigit, required this.onBack, this.leading});

  Widget _key(String d) => SizedBox(
        width: 84,
        height: 72,
        child: Material(
          color: C.card,
          shape: const CircleBorder(side: BorderSide(color: C.line)),
          child: InkWell(
            customBorder: const CircleBorder(),
            onTap: () => onDigit(d),
            child: Center(child: Text(d, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w600))),
          ),
        ),
      );

  @override
  Widget build(BuildContext context) {
    Widget row(List<Widget> c) =>
        Padding(padding: const EdgeInsets.symmetric(vertical: 8), child: Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: c));
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 36),
      child: Column(children: [
        row([_key('1'), _key('2'), _key('3')]),
        row([_key('4'), _key('5'), _key('6')]),
        row([_key('7'), _key('8'), _key('9')]),
        row([
          SizedBox(width: 84, height: 72, child: Center(child: leading)),
          _key('0'),
          SizedBox(
            width: 84,
            height: 72,
            child: IconButton(icon: const Icon(Icons.backspace_outlined, color: C.muted), onPressed: onBack),
          ),
        ]),
      ]),
    );
  }
}
