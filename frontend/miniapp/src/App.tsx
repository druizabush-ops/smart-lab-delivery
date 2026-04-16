import { useEffect, useMemo, useState } from "react";
import { MaxUI } from "@maxhub/max-ui";
import { ApiClient, ApiError } from "./api/client";
import { PatientResult, ResultsApi } from "./api/results";
import { ResultDetails } from "./components/ResultDetails";
import { ResultList } from "./components/ResultList";
import { getMaxContext, parseStartParam } from "./max/context";

export function resolvePatientApiBaseUrl(): string {
  const configuredBaseUrl = import.meta.env.VITE_PATIENT_API_BASE_URL;
  if (configuredBaseUrl && configuredBaseUrl.trim().length > 0) {
    return configuredBaseUrl;
  }
  return "/api/patient";
}

export function App(): JSX.Element {
  const context = getMaxContext();
  const start = parseStartParam(context.startParam);
  const showDebugInfo = import.meta.env.DEV;
  const baseUrl = resolvePatientApiBaseUrl();
  const api = useMemo(() => new ResultsApi(new ApiClient({ baseUrl })), []);
  const [results, setResults] = useState<PatientResult[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(start.mode === "result" ? start.resultId ?? null : null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!context.patientId) {
      setLoading(false);
      return;
    }
    api
      .list(context.patientId)
      .then((items) => {
        setResults(items);
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? `Ошибка API (${err.status ?? "n/a"})` : "Неизвестная ошибка");
      })
      .finally(() => setLoading(false));
  }, [api, context.patientId]);

  const selected = selectedId ? results.find((result) => result.result_id === selectedId) ?? null : null;

  return (
    <MaxUI>
      <main>
        <h1>Smart Lab Results</h1>
        {!context.isInsideMax ? <p>Режим вне MAX: используется fallback-контекст.</p> : null}
        <p>Platform: {context.platform} / version: {context.version}</p>
        {context.startParam ? <p>start_param: {context.startParam}</p> : null}
        {showDebugInfo ? (
          <p>
            insideMax: {String(context.isInsideMax)} / hasInitData: {String(context.hasInitData)} / patientId: {context.patientId ?? "n/a"}
          </p>
        ) : null}

        {loading ? <p>Загрузка...</p> : null}
        {!loading && !context.patientId ? <p>Не удалось определить patient_id из MAX контекста.</p> : null}
        {!loading && error ? <p>{error}</p> : null}
        {!loading && !error && context.patientId && results.length === 0 ? <p>У пациента пока нет доступных результатов.</p> : null}
        {!loading && !error && results.length > 0 && !selected ? <ResultList results={results} onOpen={setSelectedId} /> : null}
        {!loading && !error && selected ? <ResultDetails result={selected} onBack={() => setSelectedId(null)} /> : null}
      </main>
    </MaxUI>
  );
}
