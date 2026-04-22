import { useEffect, useMemo, useState } from "react";
import { MaxUI } from "@maxhub/max-ui";
import { ApiClient, ApiError } from "./api/client";
import { PatientResultDetails, PatientResultListItem, ResultsApi } from "./api/results";
import { AuthApi, PatientSession } from "./api/auth";
import { ResultDetails } from "./components/ResultDetails";
import { ResultList } from "./components/ResultList";
import { miniAppContentConfig } from "./ui/contentConfig";

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

  const getUserMessage = (error: unknown, fallback: string): string => {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        return "Сессия истекла. Войдите снова.";
      }
      if (error.status === 404) {
        return "Документ временно недоступен";
      }
      if (error.status && error.status >= 500) {
        return "Сервис временно недоступен. Попробуйте позже.";
      }
    }
    return fallback;
  };

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

  const fetchPdfBlob = async (resultId: string): Promise<Blob> => {
    const response = await fetch(`${baseUrl}/patient/results/${encodeURIComponent(resultId)}/pdf`, {
      credentials: "include",
    });
    if (!response.ok) {
      throw new ApiError("pdf_error", response.status);
    }
    return response.blob();
  };

  const openPdf = async (resultId: string): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const blob = await fetchPdfBlob(resultId);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      window.setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch (err: unknown) {
      setError(getUserMessage(err, "Не удалось открыть документ"));
    } finally {
      setBusy(false);
    }
  };

  const downloadPdf = async (resultId: string): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const blob = await fetchPdfBlob(resultId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `result-${resultId}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setError(getUserMessage(err, "PDF временно недоступен"));
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
      <main className="app-shell">
        <header className="app-header">
          <h1>{miniAppContentConfig.appTitle}</h1>
          <p>{miniAppContentConfig.appSubtitle}</p>
        </header>
        {loading ? <p>Загрузка...</p> : null}
        {!loading && !session ? (
          <section className="panel">
            <h2>Вход</h2>
            <input placeholder="Логин" value={login} onChange={(e) => setLogin(e.target.value)} />
            <input placeholder="Пароль" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <button disabled={busy} onClick={handleLoginSubmit}>Войти</button>
          </section>
        ) : null}

        {!loading && session ? (
          <section className="panel">
            <div className="welcome-card">
              <h2>{miniAppContentConfig.homeGreetingTitle} {session.patient_name || session.patient_number}!</h2>
              <p>{miniAppContentConfig.homeGreetingSubtitle}</p>
              <button onClick={handleLogout}>Выйти</button>
            </div>
            {screen === "home" ? (
              <div className="home-layout">
                <div className="home-actions">
                  <button onClick={() => setScreen("results")}>{miniAppContentConfig.homeActions.results}</button>
                  <button disabled>{miniAppContentConfig.homeActions.appointments}</button>
                  <button disabled>{miniAppContentConfig.homeActions.profile}</button>
                </div>
                <div className="placeholder-grid">
                  {miniAppContentConfig.placeholders.map((item) => (
                    <section key={item.key} className={`placeholder-card placeholder-card--${item.tone}`}>
                      <h3>{item.title}</h3>
                      <p>{item.subtitle}</p>
                    </section>
                  ))}
                </div>
              </div>
            ) : null}
            {screen === "results" ? (
              results.length === 0 ? (
                <p>{miniAppContentConfig.results.emptyState}</p>
              ) : (
                <ResultList
                  results={results}
                  onOpen={openResult}
                  onOpenPdf={(resultId) => {
                    void openPdf(resultId);
                  }}
                  onDownloadPdf={downloadPdf}
                />
              )
            ) : null}
            {screen === "details" && selected ? (
              <ResultDetails
                result={selected}
                onBack={() => setScreen("results")}
                onOpenPdf={() => {
                  void openPdf(selected.result_id);
                }}
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
