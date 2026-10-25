// Public client settings. The anon key is designed to be public:
// every table is protected by Row Level Security (owner only).
const supabaseUrl = 'https://vtsurdinopzycwsfzsuk.supabase.co';
const supabaseAnonKey =
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ0c3VyZGlub3B6eWN3c2Z6c3VrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI5NTkzMjYsImV4cCI6MjEwODUzNTMyNn0.uwS78FRbyKLiwCM07yic7SHCZ7-UaIauDo2kFUkftJQ';

/// App locks again after being in the background this long.
const lockAfter = Duration(seconds: 60);
