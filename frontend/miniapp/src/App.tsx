import { useEffect, useMemo, useState } from "react";
import { MaxUI } from "@maxhub/max-ui";
import { ApiClient, ApiError } from "./api/client";
import { PatientResultDetails, PatientResultListItem, ResultsApi } from "./api/results";
import { AuthApi, PatientSession } from "./api/auth";
import { ResultDetails } from "./components/ResultDetails";
import { ResultList } from "./components/ResultList";

type Screen = "home" | "results" | "details";

export function resolvePatientApiBaseUrl(): string {
  const configuredBaseUrl = import.meta.env.VITE_PATIENT_API_BASE_URL;
  if (configuredBaseUrl && configuredBaseUrl.trim().length > 0) {
    return configuredBaseUrl;
  }
  return "/api/patient";
}

export function App(): JSX.Element {
  const baseUrl = resolvePatientApiBaseUrl();
  const client = useMemo(() => new ApiClient({ baseUrl }), [baseUrl]);
  const resultsApi = useMemo(() => new ResultsApi(client), [client]);
  const authApi = useMemo(() => new AuthApi(client), [client]);

  const [results, setResults] = useState<PatientResultListItem[]>([]);
  const [session, setSession] = useState<PatientSession | null>(null);
  const [selected, setSelected] = useState<PatientResultDetails | null>(null);
  const [screen, setScreen] = useState<Screen>("home");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    authApi
      .me()
      .then((currentSession) => {
        setSession(currentSession);
        return resultsApi.list();
      })
      .then((items) => setResults(items))
      .catch(() => setSession(null))
      .finally(() => setLoading(false));
  }, [authApi, resultsApi]);

  const handleLoginSubmit = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const currentSession = await authApi.login(login, password);
      setSession(currentSession);
      const items = await resultsApi.list();
      setResults(items);
      setScreen("home");
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Неверный логин или пароль");
      } else {
        setError("Не удалось выполнить вход. Попробуйте позже");
      }
    } finally {
      setBusy(false);
    }
  };

  const openResult = async (resultId: string): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const details = await resultsApi.get(resultId);
      setSelected(details);
      setScreen("details");
    } catch {
      setError("Не удалось открыть результат.");
    } finally {
      setBusy(false);
    }
  };

  const openPdf = (resultId: string): void => {
    window.open(`${baseUrl}/patient/results/${encodeURIComponent(resultId)}/pdf`, "_blank", "noopener,noreferrer");
  };

  const downloadPdf = async (resultId: string): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`${baseUrl}/patient/results/${encodeURIComponent(resultId)}/pdf`, {
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error("pdf_error");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `result-${resultId}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("PDF временно недоступен");
    } finally {
      setBusy(false);
    }
  };

  const handleLogout = async (): Promise<void> => {
    await authApi.logout();
    setSession(null);
    setResults([]);
    setSelected(null);
    setScreen("home");
  };

  return (
    <MaxUI>
      <main>
        <h1>Smart Lab</h1>
        {loading ? <p>Загрузка...</p> : null}
        {!loading && !session ? (
          <section>
            <h2>Вход</h2>
            <input placeholder="Логин" value={login} onChange={(e) => setLogin(e.target.value)} />
            <input placeholder="Пароль" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <button disabled={busy} onClick={handleLoginSubmit}>Войти</button>
          </section>
        ) : null}

        {!loading && session ? (
          <section>
            <p>Здравствуйте, {session.patient_name || session.patient_number}</p>
            <button onClick={handleLogout}>Выйти</button>
            {screen === "home" ? (
              <div>
                <button onClick={() => setScreen("results")}>Результаты анализов</button>
                <button disabled>Мои записи</button>
                <button disabled>Профиль</button>
              </div>
            ) : null}
            {screen === "results" ? (
              results.length === 0 ? (
                <p>Результатов пока нет.</p>
              ) : (
                <ResultList
                  results={results}
                  onOpen={openResult}
                  onOpenPdf={openPdf}
                  onDownloadPdf={downloadPdf}
                />
              )
            ) : null}
            {screen === "details" && selected ? (
              <ResultDetails
                result={selected}
                onBack={() => setScreen("results")}
                onOpenPdf={() => openPdf(selected.result_id)}
                onDownloadPdf={() => downloadPdf(selected.result_id)}
              />
            ) : null}
          </section>
        ) : null}

        {busy ? <p>Подождите...</p> : null}
        {error ? <p>{error}</p> : null}
      </main>
    </MaxUI>
  );
}
