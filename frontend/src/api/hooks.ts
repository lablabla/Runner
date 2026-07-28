import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import type {
  Activity,
  DailyMetric,
  IntegrationStatus,
  Insight,
  PlannedWorkout,
  Summary,
  SyncResult,
  Trends,
  User,
} from "./types";

export const useMe = () => useQuery({ queryKey: ["me"], queryFn: () => api<User>("/auth/me") });

export const useSummary = () =>
  useQuery({ queryKey: ["summary"], queryFn: () => api<Summary>("/metrics/summary") });

export const useTrends = () =>
  useQuery({ queryKey: ["trends"], queryFn: () => api<Trends>("/metrics/trends") });

export const useActivities = (params: { runna_only?: boolean } = {}) =>
  useQuery({
    queryKey: ["activities", params],
    queryFn: () =>
      api<Activity[]>(`/activities?limit=100${params.runna_only ? "&runna_only=true" : ""}`),
  });

export const useActivity = (id: number) =>
  useQuery({ queryKey: ["activity", id], queryFn: () => api<Activity>(`/activities/${id}`) });

export const useDailyMetrics = (days = 60) =>
  useQuery({ queryKey: ["daily", days], queryFn: () => api<DailyMetric[]>(`/metrics/daily?days=${days}`) });

export const useIntegrations = () =>
  useQuery({ queryKey: ["integrations"], queryFn: () => api<IntegrationStatus[]>("/integrations") });

export const usePlan = () =>
  useQuery({ queryKey: ["plan"], queryFn: () => api<PlannedWorkout[]>("/plan") });

export const useInsights = () =>
  useQuery({ queryKey: ["insights"], queryFn: () => api<Insight[]>("/analysis/insights") });

export function useSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api<SyncResult>("/sync", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries(),
  });
}

export function useResyncWeather() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api<SyncResult>("/sync/weather", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries(),
  });
}

export function useConnectGarmin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { username: string; password: string }) =>
      api<IntegrationStatus>("/integrations/garmin", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["integrations"] }),
  });
}

export function useDisconnect() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (provider: string) => api<void>(`/integrations/${provider}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["integrations"] }),
  });
}

export function useGenerateWeeklySummary() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api<Insight>("/analysis/weekly-summary", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["insights"] }),
  });
}

export function useClearInsights() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api<void>("/analysis/insights", { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["insights"] }),
  });
}

export function useDeleteInsight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api<void>(`/analysis/insights/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["insights"] }),
  });
}

export function useAnalyseActivity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api<Insight>(`/analysis/activity/${id}`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["insights"] }),
  });
}

export function useCreateWorkout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<PlannedWorkout>) =>
      api<PlannedWorkout>("/plan", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan"] }),
  });
}

export function useDeleteWorkout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api<void>(`/plan/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan"] }),
  });
}

export function useImportPlanPdf() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return api<PlannedWorkout[]>("/plan/import-pdf", { method: "POST", body: form });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan"] }),
  });
}
