import 'package:supabase_flutter/supabase_flutter.dart';

SupabaseClient get sb => Supabase.instance.client;

enum Health { ok, slow, down, unknown, maintenance }

class AppStatus {
  final String id;
  final String name;
  final String short;
  final String platform;
  final String version;
  final String? healthUrl;
  final bool enabled;
  final bool maintenance;
  final String maintenanceMessage;
  final DateTime? lastCheckedAt;
  final bool? lastOk;
  final int? lastStatusCode;
  final int? lastLatencyMs;
  final String? lastError;
  final String? incidentId;
  final String? incidentTitle;
  final DateTime? incidentStartedAt;

  AppStatus.fromMap(Map<String, dynamic> m)
      : id = m['id'] as String,
        name = (m['name'] ?? '') as String,
        short = (m['short'] ?? '') as String,
        platform = (m['platform'] ?? '') as String,
        version = (m['version'] ?? '') as String,
        healthUrl = m['health_url'] as String?,
        enabled = (m['enabled'] ?? true) as bool,
        maintenance = (m['maintenance'] ?? false) as bool,
        maintenanceMessage = (m['maintenance_message'] ?? '') as String,
        lastCheckedAt = _dt(m['last_checked_at']),
        lastOk = m['last_ok'] as bool?,
        lastStatusCode = m['last_status_code'] as int?,
        lastLatencyMs = m['last_latency_ms'] as int?,
        lastError = m['last_error'] as String?,
        incidentId = m['open_incident_id'] as String?,
        incidentTitle = m['open_incident_title'] as String?,
        incidentStartedAt = _dt(m['open_incident_started_at']);

  Health get health {
    if (maintenance) return Health.maintenance;
    if (incidentId != null) return Health.down;
    if (healthUrl == null || lastOk == null) return Health.unknown;
    if (lastOk == false) return Health.down;
    if ((lastLatencyMs ?? 0) > 2000) return Health.slow;
    return Health.ok;
  }

  String get initials => short.isNotEmpty
      ? short
      : name.trim().split(RegExp(r'\s+')).take(2).map((w) => w.isEmpty ? '' : w[0].toUpperCase()).join();
}

class CheckRow {
  final DateTime at;
  final bool ok;
  final int? statusCode;
  final int? latencyMs;
  final String? error;
  CheckRow.fromMap(Map<String, dynamic> m)
      : at = _dt(m['checked_at'])!,
        ok = m['ok'] as bool,
        statusCode = m['status_code'] as int?,
        latencyMs = m['latency_ms'] as int?,
        error = m['error'] as String?;
}

class IncidentRow {
  final String id;
  final String appId;
  final String title;
  final String? lastError;
  final int failCount;
  final DateTime startedAt;
  final DateTime? resolvedAt;
  IncidentRow.fromMap(Map<String, dynamic> m)
      : id = m['id'] as String,
        appId = m['app_id'] as String,
        title = (m['title'] ?? '') as String,
        lastError = m['last_error'] as String?,
        failCount = (m['fail_count'] ?? 1) as int,
        startedAt = _dt(m['started_at'])!,
        resolvedAt = _dt(m['resolved_at']);
}

DateTime? _dt(dynamic v) => v == null ? null : DateTime.parse(v as String).toLocal();

class Api {
  static Future<List<AppStatus>> apps() async {
    final rows = await sb.from('app_status').select().order('sort').order('created_at');
    return (rows as List).map((r) => AppStatus.fromMap(r as Map<String, dynamic>)).toList();
  }

  static Future<List<CheckRow>> checks(String appId, {int limit = 30}) async {
    final rows = await sb
        .from('checks')
        .select()
        .eq('app_id', appId)
        .order('checked_at', ascending: false)
        .limit(limit);
    return (rows as List).map((r) => CheckRow.fromMap(r as Map<String, dynamic>)).toList();
  }

  static Future<List<IncidentRow>> incidents({int limit = 50}) async {
    final rows = await sb.from('incidents').select().order('started_at', ascending: false).limit(limit);
    return (rows as List).map((r) => IncidentRow.fromMap(r as Map<String, dynamic>)).toList();
  }

  static Future<void> checkNow([String? appId]) async {
    await sb.functions.invoke('health-check', body: {if (appId != null) 'app_id': appId});
  }

  static Future<void> log(String? appId, String action, [String? note]) async {
    await sb.from('action_log').insert({'app_id': appId, 'action': action, 'note': note});
  }

  static Future<void> setMaintenance(String appId, bool on) async {
    await sb.from('apps').update({'maintenance': on}).eq('id', appId);
    await log(appId, on ? 'maintenance_on' : 'maintenance_off');
  }

  static Future<void> resolveIncident(String incidentId, String appId) async {
    await sb.from('incidents').update({'resolved_at': DateTime.now().toUtc().toIso8601String()}).eq('id', incidentId);
    await log(appId, 'incident_resolved_manually');
  }

  static Future<void> saveApp({
    String? id,
    required String name,
    required String short,
    required String platform,
    required String version,
    String? healthUrl,
  }) async {
    final data = {
      'name': name,
      'short': short,
      'platform': platform,
      'version': version,
      'health_url': (healthUrl == null || healthUrl.trim().isEmpty) ? null : healthUrl.trim(),
    };
    if (id == null) {
      await sb.from('apps').insert(data);
    } else {
      await sb.from('apps').update(data).eq('id', id);
    }
  }

  static Future<Map<String, dynamic>> billing() async {
    final r = await sb.from('owner_billing').select().eq('id', 1).maybeSingle();
    return r ?? <String, dynamic>{};
  }

  static Future<void> saveBilling(Map<String, dynamic> data) async {
    await sb.from('owner_billing').upsert({
      'id': 1,
      ...data,
      'updated_at': DateTime.now().toUtc().toIso8601String(),
    });
  }

  /// Smart Sistem loginlari (smart-staff edge function). Xato bo'lsa — tushunarli matn bilan Exception.
  static Future<Map<String, dynamic>> smartStaff(Map<String, dynamic> body) async {
    try {
      final r = await sb.functions.invoke('smart-staff', body: body);
      final d = (r.data is Map) ? Map<String, dynamic>.from(r.data as Map) : <String, dynamic>{};
      if (d['ok'] != true) throw StaffXato((d['error'] ?? 'Xato').toString());
      return d;
    } on FunctionException catch (e) {
      final det = e.details;
      final msg = det is Map ? (det['error'] ?? det.toString()).toString() : (det?.toString() ?? 'HTTP ${e.status}');
      throw StaffXato(msg);
    }
  }

  static Future<List<Map<String, dynamic>>> smartRestoranlar() async {
    final d = await smartStaff({'op': 'list'});
    return ((d['restaurants'] as List?) ?? const []).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  static Future<void> deleteApp(String id) async {
    await sb.from('apps').delete().eq('id', id);
  }
}

class StaffXato implements Exception {
  StaffXato(this.msg);
  final String msg;
  @override
  String toString() => msg;
}
