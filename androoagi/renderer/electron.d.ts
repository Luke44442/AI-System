export {};

declare global {
  interface Window {
    electronAPI: {
      minimize: () => void;
      maximize: () => void;
      close: () => void;

      getSettings: () => Promise<{ apiKey: string }>;
      saveSettings: (data: { apiKey: string }) => Promise<{ ok: boolean }>;

      listCycles: () => Promise<unknown[]>;
      getCycle: (id: string) => Promise<unknown>;
      clearCycles: () => Promise<{ ok: boolean }>;

      getStats: () => Promise<{ totalOppsFound: number; totalCycles: number; readyToLaunch: number }>;

      startCycle: (opts: { mode: string; focusNiche?: string | null }) => void;
      stopCycle: () => void;

      updateApproval: (payload: { cycleId: string; itemId: string; action: string }) => Promise<{ ok: boolean; cycle?: unknown }>;

      openExternal: (url: string) => void;

      on: (channel: string, fn: (...args: unknown[]) => void) => (() => void) | undefined;
      once: (channel: string, fn: (...args: unknown[]) => void) => void;
    };
  }
}
