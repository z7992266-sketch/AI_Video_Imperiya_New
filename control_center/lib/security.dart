import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

class Security {
  static const _storage = FlutterSecureStorage(aOptions: AndroidOptions(encryptedSharedPreferences: true));
  static const _pinKey = 'cc_pin';
  static const _failKey = 'cc_pin_fail';
  static const _lockUntilKey = 'cc_lock_until';
  static final _auth = LocalAuthentication();

  static Future<bool> hasPin() async => (await _storage.read(key: _pinKey)) != null;

  static Future<void> setPin(String pin) => _storage.write(key: _pinKey, value: pin);

  static Future<void> clear() async {
    await _storage.delete(key: _pinKey);
    await _storage.delete(key: _failKey);
    await _storage.delete(key: _lockUntilKey);
  }

  /// Seconds the user must still wait after too many wrong PINs (0 = may try).
  static Future<int> lockedSeconds() async {
    final v = await _storage.read(key: _lockUntilKey);
    if (v == null) return 0;
    final until = DateTime.fromMillisecondsSinceEpoch(int.parse(v));
    final left = until.difference(DateTime.now()).inSeconds;
    return left > 0 ? left : 0;
  }

  /// Returns true when the PIN is right. 5 wrong tries → 60 s lock, then doubles.
  static Future<bool> checkPin(String pin) async {
    if (await lockedSeconds() > 0) return false;
    final saved = await _storage.read(key: _pinKey);
    if (saved != null && saved == pin) {
      await _storage.delete(key: _failKey);
      return true;
    }
    final fails = int.tryParse(await _storage.read(key: _failKey) ?? '0') ?? 0;
    final next = fails + 1;
    await _storage.write(key: _failKey, value: '$next');
    if (next % 5 == 0) {
      final secs = 60 * (1 << ((next ~/ 5) - 1)).clamp(1, 32);
      await _storage.write(
        key: _lockUntilKey,
        value: '${DateTime.now().add(Duration(seconds: secs)).millisecondsSinceEpoch}',
      );
    }
    return false;
  }

  static Future<bool> canBiometric() async {
    try {
      return await _auth.canCheckBiometrics && await _auth.isDeviceSupported();
    } on PlatformException {
      return false;
    }
  }

  static Future<bool> biometric() async {
    try {
      return await _auth.authenticate(
        localizedReason: 'Control Center\'ga kirish uchun tasdiqlang',
        options: const AuthenticationOptions(biometricOnly: true, stickyAuth: true),
      );
    } on PlatformException {
      return false;
    }
  }
}
