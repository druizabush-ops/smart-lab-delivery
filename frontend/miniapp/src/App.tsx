import { useEffect, useMemo, useState } from "react";
import { MaxUI } from "@maxhub/max-ui";
import { ApiClient, ApiError } from "./api/client";
import { PatientResult, ResultsApi } from "./api/results";
import { AuthApi, PatientSession } from "./api/auth";
import { ResultDetails } from "./components/ResultDetails";
import { ResultList } from "./components/ResultList";
import { getMaxContext, parseStartParam } from "./max/context";

type AuthMode = "chooser" | "login" | "phone" | "code";

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
  const baseUrl = resolvePatientApiBaseUrl();
  const client = useMemo(() => new ApiClient({ baseUrl }), [baseUrl]);
  const resultsApi = useMemo(() => new ResultsApi(client), [client]);
  const authApi = useMemo(() => new AuthApi(client), [client]);
  const [results, setResults] = useState<PatientResult[]>([]);
  const [session, setSession] = useState<PatientSession | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(start.mode === "result" ? start.resultId ?? null : null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("chooser");
  const [pendingPatientId, setPendingPatientId] = useState<string>("");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");

  useEffect(() => {
    authApi
      .me()
      .then((currentSession) => {
        setSession(currentSession);
        return resultsApi.list();
      })
      .then((items) => setResults(items))
      .catch(() => {
        setSession(null);
      })
      .finally(() => setLoading(false));
  }, [authApi, resultsApi]);

  const selected = selectedId ? results.find((result) => result.result_id === selectedId) ?? null : null;

  const handleLoginSubmit = async (): Promise<void> => {
    try {
      setError(null);
      const currentSession = await authApi.login(login, password);
      setSession(currentSession);
      const items = await resultsApi.list();
      setResults(items);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? "Неверный логин/пароль" : "Ошибка входа");
    }
  };

  const handlePhoneSubmit = async (): Promise<void> => {
    try {
      setError(null);
      const pending = await authApi.loginByPhone(phone);
      setPendingPatientId(pending.patient_id);
      setAuthMode("code");
    } catch {
      setError("Ошибка входа по телефону");
    }
  };

  const handleCodeSubmit = async (): Promise<void> => {
    try {
      setError(null);
      const currentSession = await authApi.confirmCode(pendingPatientId, code);
      setSession(currentSession);
      const items = await resultsApi.list();
      setResults(items);
    } catch {
      setError("Неверный SMS-код");
    }
  };

  const handleLogout = async (): Promise<void> => {
    await authApi.logout();
    setSession(null);
    setResults([]);
    setSelectedId(null);
    setAuthMode("chooser");
  };

  return (
    <MaxUI>
      <main>
        <h1>Smart Lab Results</h1>
        {!context.isInsideMax ? <p>Режим вне MAX: используется fallback-контекст.</p> : null}
        {loading ? <p>Загрузка...</p> : null}
        {!loading && !session ? (
          <section>
            <h2>Вход пациента</h2>
            {authMode === "chooser" ? (
              <>
                <button onClick={() => setAuthMode("login")}>Вход по логину</button>
                <button onClick={() => setAuthMode("phone")}>Вход по телефону</button>
              </>
            ) : null}
            {authMode === "login" ? (
              <>
                <input placeholder="Логин" value={login} onChange={(e) => setLogin(e.target.value)} />
                <input placeholder="Пароль" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
                <button onClick={handleLoginSubmit}>Войти</button>
              </>
            ) : null}
            {authMode === "phone" ? (
              <>
                <input placeholder="Телефон" value={phone} onChange={(e) => setPhone(e.target.value)} />
                <button onClick={handlePhoneSubmit}>Получить код</button>
              </>
            ) : null}
            {authMode === "code" ? (
              <>
                <input placeholder="SMS-код" value={code} onChange={(e) => setCode(e.target.value)} />
                <button onClick={handleCodeSubmit}>Подтвердить код</button>
              </>
            ) : null}
          </section>
        ) : null}

        {!loading && session ? (
          <section>
            <p>Пациент: {session.patient_name || session.patient_number}</p>
            <button onClick={handleLogout}>Выйти</button>
            {error ? <p>{error}</p> : null}
            {!error && results.length === 0 ? <p>У пациента пока нет доступных результатов.</p> : null}
            {!error && results.length > 0 && !selected ? <ResultList results={results} onOpen={setSelectedId} /> : null}
            {!error && selected ? <ResultDetails result={selected} onBack={() => setSelectedId(null)} /> : null}
          </section>
        ) : null}

        {error ? <p>{error}</p> : null}
      </main>
    </MaxUI>
  );
}
