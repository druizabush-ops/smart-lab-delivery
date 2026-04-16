export type MaxContext = {
  isInsideMax: boolean;
  hasInitData: boolean;
  hasUser: boolean;
  hasStartParam: boolean;
  initData: string | null;
  initDataUnsafe: {
    start_param?: string;
    user?: { id?: string | number };
  } | null;
  startParam: string | null;
  platform: string;
  version: string;
  patientId: string | null;
};

declare global {
  interface Window {
    WebApp?: {
      initData?: string;
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
  const initData = webApp?.initData ?? null;
  const initDataUnsafe = webApp?.initDataUnsafe ?? null;
  const startParam = initDataUnsafe?.start_param ?? null;
  const userId = initDataUnsafe?.user?.id;
  const hasUser = userId !== null && userId !== undefined;
  return {
    isInsideMax: Boolean(webApp),
    hasInitData: Boolean(initData),
    hasUser,
    hasStartParam: Boolean(startParam),
    initData,
    initDataUnsafe,
    startParam,
    platform: webApp?.platform ?? "web",
    version: webApp?.version ?? "0",
    patientId: hasUser ? String(userId) : null,
  };
}

export function parseStartParam(startParam: string | null): { mode: "list" | "result"; resultId?: string } {
  if (!startParam) return { mode: "list" };
  if (startParam.startsWith("result:")) {
    return { mode: "result", resultId: startParam.replace("result:", "") };
  }
  return { mode: "list" };
}
