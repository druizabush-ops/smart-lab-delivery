export function getMaxContext() {
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
export function parseStartParam(startParam) {
    if (!startParam)
        return { mode: "list" };
    if (startParam.startsWith("result:")) {
        return { mode: "result", resultId: startParam.replace("result:", "") };
    }
    return { mode: "list" };
}
