export interface User {
  id: number;
  email: string;
  display_name: string | null;
  home_lat: number | null;
  home_lon: number | null;
  is_admin: boolean;
  created_at: string;
}

export interface Weather {
  temp_c: number | null;
  apparent_temp_c: number | null;
  humidity_pct: number | null;
  wind_speed_kmh: number | null;
  precip_mm: number | null;
  summary: string | null;
}

export interface Activity {
  id: number;
  source: string;
  name: string | null;
  sport_type: string;
  start_time: string;
  distance_m: number | null;
  duration_s: number | null;
  avg_pace_s_per_km: number | null;
  avg_hr: number | null;
  max_hr: number | null;
  elevation_gain_m: number | null;
  aerobic_te: number | null;
  is_runna: boolean;
  difficulty_score: number | null;
  difficulty_breakdown: Record<string, number | Record<string, number>> | null;
  weather: Weather | null;
}

export interface DailyMetric {
  date: string;
  sleep_seconds: number | null;
  sleep_score: number | null;
  resting_hr: number | null;
  hrv_overnight: number | null;
  stress_avg: number | null;
  body_battery_high: number | null;
  body_battery_low: number | null;
  steps: number | null;
  training_readiness: number | null;
}

export interface ACWR {
  acute: number;
  chronic: number;
  ratio: number | null;
  zone: string;
}

export interface Summary {
  total_runs: number;
  total_distance_km: number;
  this_week_km: number;
  acwr: ACWR;
  latest_readiness: number | null;
}

export interface Trends {
  weekly_mileage: { week: string; distance_km: number; duration_h: number; runs: number; avg_difficulty: number | null }[];
  acwr: ACWR;
  aerobic_efficiency: { date: string; efficiency_index: number }[];
  sleep_vs_performance: { date: string; sleep_score: number; difficulty_score: number; body_battery_high: number | null }[];
}

export interface PlannedWorkout {
  id: number;
  date: string;
  workout_type: string;
  title: string | null;
  description: string | null;
  distance_target_m: number | null;
  duration_target_s: number | null;
  source: string;
  completed_activity_id: number | null;
}

export interface IntegrationStatus {
  provider: string;
  status: string;
  status_detail: string | null;
  last_sync_at: string | null;
}

export interface Insight {
  id: number;
  kind: string;
  period: string | null;
  content: string;
  model: string | null;
  created_at: string;
}

export interface SyncResult {
  activities_added: number;
  activities_updated: number;
  daily_metrics_upserted: number;
  weather_enriched: number;
  errors: string[];
}
