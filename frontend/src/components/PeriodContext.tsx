"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AcademicPeriod } from "@/lib/types";

interface PeriodContextValue {
  periods: AcademicPeriod[];
  activePeriod: AcademicPeriod | null;
  loading: boolean;
  error: string | null;
  selectPeriod: (id: number) => Promise<void>;
  refreshPeriods: () => Promise<void>;
}

const PeriodContext = createContext<PeriodContextValue>({
  periods: [],
  activePeriod: null,
  loading: true,
  error: null,
  selectPeriod: async () => {},
  refreshPeriods: async () => {},
});

export function PeriodProvider({ children }: { children: React.ReactNode }) {
  const [periods, setPeriods] = useState<AcademicPeriod[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshPeriods = useCallback(async () => {
    try {
      setError(null);
      const list = await api.listPeriods();
      setPeriods(list);
      setSelectedId((prev) => {
        if (prev && list.some((p) => p.id === prev)) return prev;
        const active = list.find((p) => p.is_active) || list[0];
        return active ? active.id : null;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat periode akademik");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshPeriods();
  }, [refreshPeriods]);

  const selectPeriod = useCallback(async (id: number) => {
    setSelectedId(id);
    try {
      await api.activatePeriod(id);
      await refreshPeriods();
    } catch {
      // Keep local selection even if activation call fails
    }
  }, [refreshPeriods]);

  const activePeriod =
    periods.find((p) => p.id === selectedId) ||
    periods.find((p) => p.is_active) ||
    periods[0] ||
    null;

  return (
    <PeriodContext.Provider
      value={{ periods, activePeriod, loading, error, selectPeriod, refreshPeriods }}
    >
      {children}
    </PeriodContext.Provider>
  );
}

export function usePeriod() {
  return useContext(PeriodContext);
}
