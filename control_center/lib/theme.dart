import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class C {
  static const bg = Color(0xFF0B0B0C);
  static const card = Color(0xFF151517);
  static const line = Color(0xFF2A2A2E);
  static const gold = Color(0xFFF2D27A);
  static const goldDeep = Color(0xFFC9962F);
  static const goldDim = Color(0xFF4A3C1C);
  static const goldBg = Color(0xFF1F1A10);
  static const text = Color(0xFFF5F1E8);
  static const muted = Color(0xFFA39F95);
  static const ok = Color(0xFF3FBF7F);
  static const warn = Color(0xFFF0A13A);
  static const bad = Color(0xFFE5484D);
  static const badBg = Color(0xFF2A1416);
  static const badLine = Color(0xFF5C2226);

  static const goldGradient = LinearGradient(
    colors: [gold, goldDeep],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}

ThemeData buildTheme() {
  final base = ThemeData.dark(useMaterial3: true);
  final textTheme = GoogleFonts.manropeTextTheme(base.textTheme).apply(
    bodyColor: C.text,
    displayColor: C.text,
  );
  return base.copyWith(
    scaffoldBackgroundColor: C.bg,
    colorScheme: base.colorScheme.copyWith(
      primary: C.gold,
      secondary: C.goldDeep,
      surface: C.card,
      error: C.bad,
    ),
    textTheme: textTheme,
    appBarTheme: AppBarTheme(
      backgroundColor: C.bg,
      foregroundColor: C.text,
      elevation: 0,
      titleTextStyle: textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: C.card,
      labelStyle: const TextStyle(color: C.muted),
      hintStyle: const TextStyle(color: C.muted),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: C.line),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: C.line),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: C.gold),
      ),
    ),
    snackBarTheme: const SnackBarThemeData(
      backgroundColor: C.card,
      contentTextStyle: TextStyle(color: C.text),
      behavior: SnackBarBehavior.floating,
    ),
    dividerColor: C.line,
  );
}
