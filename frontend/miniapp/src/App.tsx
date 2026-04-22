import { useEffect, useMemo, useState } from "react";
import { MaxUI } from "@maxhub/max-ui";
import { ApiClient, ApiError } from "./api/client";
import { PatientResultDetails, PatientResultListItem, ResultsApi } from "./api/results";
import { AuthApi, PatientSession } from "./api/auth";
import { ResultDetails } from "./components/ResultDetails";
import { ResultList } from "./components/ResultList";
import { miniAppContentConfig } from "./ui/contentConfig";
import { getMaxContext } from "./max/context";

type Screen = "home" | "results" | "details" | "pdf";
type PdfViewerSource = "results" | "details";
type PdfViewerState = {
  resultId: string;
  source: PdfViewerSource;
};

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
  const [pdfViewer, setPdfViewer] = useState<PdfViewerState | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const maxContext = useMemo(() => getMaxContext(), []);

  const resolvePatientDisplayName = (rawName: string, fallbackNumber: string): string => {
    const parts = rawName.split(/\s+/).map((part) => part.trim()).filter(Boolean);
    if (parts.length >= 3) {
      return `${parts[1]} ${parts[2]}`;
    }
    if (parts.length >= 1) {
      return parts[0];
    }
    return fallbackNumber;
  };

  const getUserMessage = (rawError: unknown, fallback: string): string => {
    if (rawError instanceof ApiError) {
      if (rawError.status === 401) {
        return "Сессия истекла. Войдите снова.";
      }
      if (rawError.status === 404) {
        return "Документ временно недоступен";
      }
      if (rawError.status && rawError.status >= 500) {
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
    setInfoMessage(null);
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

  const buildPdfUrl = (resultId: string, mode: "inline" | "attachment"): string => (
    `${baseUrl}/patient/results/${encodeURIComponent(resultId)}/pdf?disposition=${mode}`
  );

  const fetchPdfBlob = async (resultId: string): Promise<Blob> => {
    const response = await fetch(buildPdfUrl(resultId, "inline"), {
      credentials: "include",
    });
    if (!response.ok) {
      throw new ApiError("pdf_error", response.status);
    }
    return response.blob();
  };

  const openPdfViewer = (resultId: string, source: PdfViewerSource): void => {
    setError(null);
    setInfoMessage(null);
    setPdfViewer({ resultId, source });
    setScreen("pdf");
  };

  const closePdfViewer = (): void => {
    if (pdfViewer?.source === "details") {
      setScreen("details");
      return;
    }
    setScreen("results");
  };

  const savePdf = async (resultId: string): Promise<void> => {
    setBusy(true);
    setError(null);
    setInfoMessage(null);
    try {
      const blob = await fetchPdfBlob(resultId);
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      const supportsDownloadAttribute = "download" in link;
      if (!supportsDownloadAttribute) {
        window.location.assign(buildPdfUrl(resultId, "attachment"));
        return;
      }
      link.href = objectUrl;
      link.download = `result-${resultId}.pdf`;
      link.rel = "noopener noreferrer";
      link.click();
      setInfoMessage("PDF подготовлен к сохранению на устройство.");
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1_000);
    } catch (err: unknown) {
      setError(getUserMessage(err, "Документ временно недоступен"));
    } finally {
      setBusy(false);
    }
  };

  const sharePdf = async (resultId: string): Promise<void> => {
    setBusy(true);
    setError(null);
    setInfoMessage(null);
    try {
      const blob = await fetchPdfBlob(resultId);
      const file = new File([blob], `result-${resultId}.pdf`, { type: "application/pdf" });
      const shareUrl = buildPdfUrl(resultId, "inline");
      if (navigator.share) {
        const canShareFiles = navigator.canShare ? navigator.canShare({ files: [file] }) : false;
        if (canShareFiles) {
          await navigator.share({
            title: "Результат анализа",
            text: "PDF с результатом анализа",
            files: [file],
          });
          return;
        }
        await navigator.share({
          title: "Результат анализа",
          text: "PDF с результатом анализа",
          url: shareUrl,
        });
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(shareUrl);
        setInfoMessage("Системный share недоступен. Ссылка на PDF скопирована в буфер обмена.");
        return;
      }
      setInfoMessage("Системный share недоступен в текущем runtime. Откройте PDF и отправьте ссылку вручную.");
    } catch (err: unknown) {
      setError(getUserMessage(err, "Не удалось открыть share-меню для PDF"));
    } finally {
      setBusy(false);
    }
  };

  const sendPdfToMax = async (resultId: string): Promise<void> => {
    setBusy(true);
    setError(null);
    setInfoMessage(null);
    try {
      const shareUrl = buildPdfUrl(resultId, "inline");
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(shareUrl);
      }
      const botName = import.meta.env.VITE_MAX_BOT_NAME;
      if (botName && botName.length > 0) {
        window.open(`https://max.ru/${botName}`, "_blank", "noopener,noreferrer");
      }
      if (maxContext.isInsideMax) {
        setInfoMessage("API отправки файла в чат MAX не подтверждено в runtime. Ссылка скопирована, отправьте документ вручную в чат.");
      } else {
        setInfoMessage("Функция прямой отправки в MAX работает как foundation: ссылка на PDF скопирована, отправьте её в MAX вручную.");
      }
    } catch {
      setInfoMessage("Прямая отправка PDF в MAX пока недоступна: скопируйте ссылку и отправьте документ вручную.");
    } finally {
      setBusy(false);
    }
  };

  const handleLogout = async (): Promise<void> => {
    await authApi.logout();
    setSession(null);
    setResults([]);
    setSelected(null);
    setPdfViewer(null);
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
            {screen !== "pdf" ? (
              <div className="welcome-card">
                <h2>{miniAppContentConfig.homeGreetingTitle}, {resolvePatientDisplayName(session.patient_name, session.patient_number)}!</h2>
                <p>{miniAppContentConfig.homeGreetingSubtitle}</p>
                <button onClick={handleLogout}>Выйти</button>
              </div>
            ) : null}
            {screen === "home" ? (
              <div className="home-layout">
                <button className="home-results-cta" onClick={() => setScreen("results")}>
                  <h3>{miniAppContentConfig.homeActions.results}</h3>
                  <p>Откройте список результатов и подробные показатели.</p>
                </button>
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
                    openPdfViewer(resultId, "results");
                  }}
                  onDownloadPdf={(resultId) => {
                    void savePdf(resultId);
                  }}
                />
              )
            ) : null}
            {screen === "details" && selected ? (
              <ResultDetails
                result={selected}
                onBack={() => setScreen("results")}
                onOpenPdf={() => {
                  openPdfViewer(selected.result_id, "details");
                }}
                onDownloadPdf={() => {
                  void savePdf(selected.result_id);
                }}
              />
            ) : null}
            {screen === "pdf" && pdfViewer ? (
              <section className="pdf-viewer" aria-label="Экран просмотра PDF">
                <header className="pdf-viewer__topbar">
                  <button type="button" onClick={closePdfViewer}>{miniAppContentConfig.pdfViewer.backButton}</button>
                  <strong>{miniAppContentConfig.pdfViewer.title}</strong>
                  <button type="button" onClick={() => { void handleLogout(); }}>{miniAppContentConfig.pdfViewer.logoutButton}</button>
                </header>
                <div className="pdf-viewer__content">
                  <iframe
                    title="PDF документа"
                    src={buildPdfUrl(pdfViewer.resultId, "inline")}
                    className="pdf-viewer__frame"
                  />
                </div>
                <footer className="pdf-viewer__actions">
                  <button type="button" onClick={() => { void savePdf(pdfViewer.resultId); }}>
                    {miniAppContentConfig.pdfViewer.saveButton}
                  </button>
                  <button type="button" onClick={() => { void sharePdf(pdfViewer.resultId); }}>
                    {miniAppContentConfig.pdfViewer.shareButton}
                  </button>
                  <button type="button" onClick={() => { void sendPdfToMax(pdfViewer.resultId); }}>
                    {miniAppContentConfig.pdfViewer.sendToMaxButton}
                  </button>
                </footer>
              </section>
            ) : null}
          </section>
        ) : null}

        {busy ? <p>Подождите...</p> : null}
        {error ? <p>{error}</p> : null}
        {infoMessage ? <p>{infoMessage}</p> : null}
      </main>
    </MaxUI>
  );
}
