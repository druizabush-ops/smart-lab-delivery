export type MaxContext = {
  isInsideMax: boolean;
  startParam: string | null;
  platform: string;
  version: string;
  patientId: string | null;
};

declare global {
  interface Window {
    WebApp?: {
      initDataUnsafe?: {
        start_param?: string;
        user?: { id?: string | number };
      };
      platform?: string;
      version?: string;
    };
  }
}

export function getMaxContext(): MaxContext {
  const webApp = window.WebApp;
  const startParam = webApp?.initDataUnsafe?.start_param ?? null;
  const userId = webApp?.initDataUnsafe?.user?.id;
  return {
    isInsideMax: Boolean(webApp),
    startParam,
    platform: webApp?.platform ?? "web",
    version: webApp?.version ?? "0",
    patientId: userId ? String(userId) : null,
  };
}

export function parseStartParam(startParam: string | null): { mode: "list" | "result"; resultId?: string } {
  if (!startParam) return { mode: "list" };
  if (startParam.startsWith("result:")) {
    return { mode: "result", resultId: startParam.replace("result:", "") };
  }
  return { mode: "list" };
}
