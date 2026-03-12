import useSWR from "swr";
import api from "@/lib/api";
import type { Verification, PaginatedResponse } from "@/types";

const fetcher = (url: string) => api.get(url).then((res) => res.data);

export function useVerifications(params?: {
  page?: number;
  page_size?: number;
  module?: string;
  status?: string;
}) {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.page_size) searchParams.set("page_size", String(params.page_size));
  if (params?.module) searchParams.set("module", params.module);
  if (params?.status) searchParams.set("status", params.status);

  const query = searchParams.toString();
  const url = `/verifications${query ? `?${query}` : ""}`;

  const { data, error, isLoading, mutate } = useSWR<PaginatedResponse<Verification>>(
    url,
    fetcher,
    { revalidateOnFocus: false }
  );

  return { verifications: data, error, isLoading, mutate };
}

export function useVerification(id: string) {
  const { data, error, isLoading, mutate } = useSWR<Verification>(
    id ? `/verifications/${id}` : null,
    fetcher
  );

  return { verification: data, error, isLoading, mutate };
}

export function useDashboardStats() {
  const { data, error, isLoading } = useSWR("/dashboard/stats", fetcher, {
    revalidateOnFocus: false,
    refreshInterval: 30000,
  });

  return { stats: data, error, isLoading };
}
