import { useEffect, useMemo, useState } from "react";
import { MaxUI } from "@maxhub/max-ui";
import { ApiClient, ApiError } from "./api/client";
import { PatientResultDetails, PatientResultListItem, ResultsApi } from "./api/results";
import { AuthApi, PatientSession } from "./api/auth";
import { buildPatientIndicators } from "./utils/patientResults";
import { MainTab, miniAppContentConfig, ServiceCategory, ServiceTreeNode } from "./ui/contentConfig";

type Route =
  | { kind: "tab"; tab: MainTab }
  | { kind: "result-details"; resultId: string }
  | { kind: "pdf"; resultId: string };

type ExtendedSession = PatientSession;

const asset = (name: string): string => `/assets/${name}`;

const tabIconById: Record<MainTab, string> = {
  home: asset("icon-home.svg"),
  results: asset("icon-analyses.svg"),
  appointment: asset("icon-appointment.svg"),
  loyalty: asset("icon-promos.svg"),
  services: asset("icon-services.svg"),
};

const sectionAssetById: Record<MainTab, string> = {
  home: asset("icon-home.svg"),
  results: asset("card-analyses.png"),
  appointment: asset("card-appointment.png"),
  loyalty: asset("card-promos.png"),
  services: asset("card-services.png"),
};

export function resolvePatientApiBaseUrl(): string {
  const configuredBaseUrl = import.meta.env.VITE_PATIENT_API_BASE_URL;
  return configuredBaseUrl && configuredBaseUrl.trim().length > 0 ? configuredBaseUrl : "/api/patient";
}

function collectMatches(node: ServiceTreeNode, query: string): ServiceTreeNode | null {
  const lower = query.toLowerCase();
  const selfMatched = node.name.toLowerCase().includes(lower);
  const children = (node.children ?? [])
    .map((child) => collectMatches(child, query))
    .filter((child): child is ServiceTreeNode => Boolean(child));

  if (selfMatched || children.length > 0) {
    return {
      ...node,
      children: children.length > 0 ? children : node.children,
    };
  }
  return null;
}

function filterCategory(category: ServiceCategory, query: string): ServiceCategory | null {
  if (!query.trim()) {
    return category;
  }
  const nextTree = category.tree
    .map((node) => collectMatches(node, query))
    .filter((node): node is ServiceTreeNode => Boolean(node));
  if (category.name.toLowerCase().includes(query.toLowerCase()) || nextTree.length > 0) {
    return { ...category, tree: nextTree.length > 0 ? nextTree : category.tree };
  }
  return null;
}

function normalizeProfileField(value: string | null | undefined): string {
  const text = value?.trim();
  return text && text !== "—" ? text : "не указана";
}

function initials(name: string): string {
  const letters = name
    .split(" ")
    .map((part) => part.trim()[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("");
  return letters || "С";
}

function statusTone(status: string): "ready" | "processing" | "error" {
  const lower = status.toLowerCase();
  if (lower.includes("готов")) return "ready";
  if (lower.includes("ошиб") || lower.includes("отмен")) return "error";
  return "processing";
}

export function App(): JSX.Element {
  const baseUrl = resolvePatientApiBaseUrl();
  const client = useMemo(() => new ApiClient({ baseUrl }), [baseUrl]);
  const authApi = useMemo(() => new AuthApi(client), [client]);
  const resultsApi = useMemo(() => new ResultsApi(client), [client]);

  const [session, setSession] = useState<ExtendedSession | null>(null);
  const [results, setResults] = useState<PatientResultListItem[]>([]);
  const [selected, setSelected] = useState<PatientResultDetails | null>(null);
  const [route, setRoute] = useState<Route>({ kind: "tab", tab: "home" });
  const [history, setHistory] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [profileExpanded, setProfileExpanded] = useState(false);

  const [servicesQuery, setServicesQuery] = useState("");
  const [selectedCategoryId, setSelectedCategoryId] = useState(miniAppContentConfig.services.categories[0]?.id ?? "");
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  useEffect(() => {
    authApi
      .me()
      .then((currentSession) => {
        setSession(currentSession as ExtendedSession);
        return resultsApi.list();
      })
      .then(setResults)
      .catch(() => setSession(null))
      .finally(() => setLoading(false));
  }, [authApi, resultsApi]);

  const patientName = session?.patient_name ?? "";
  const greetingName = patientName.split(" ").slice(1, 3).join(" ") || patientName || "пациент";
  const phone = session?.patient_phone ?? session?.phone ?? miniAppContentConfig.clinicPhone;
  const email = session?.email ?? null;
  const birthDate = normalizeProfileField(session?.birth_date);

  const openRoute = (nextRoute: Route): void => {
    setHistory((prev) => [...prev, route]);
    setRoute(nextRoute);
    setError(null);
    setInfoMessage(null);
  };

  const openTab = (tab: MainTab): void => {
    setRoute({ kind: "tab", tab });
    setError(null);
    setInfoMessage(null);
  };

  const goBack = (): void => {
    setHistory((prev) => {
      const copy = [...prev];
      const previous = copy.pop();
      if (previous) {
        setRoute(previous);
      }
      return copy;
    });
  };

  const handleLoginSubmit = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const nextSession = await authApi.login(login, password);
      setSession(nextSession as ExtendedSession);
      setResults(await resultsApi.list());
      setRoute({ kind: "tab", tab: "home" });
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) {
        setError(miniAppContentConfig.login.invalidCredentialsMessage);
      } else {
        setError(miniAppContentConfig.login.genericErrorMessage);
      }
    } finally {
      setBusy(false);
    }
  };

  const handleLogout = async (): Promise<void> => {
    await authApi.logout();
    setSession(null);
    setResults([]);
    setSelected(null);
    setHistory([]);
    setRoute({ kind: "tab", tab: "home" });
  };

  const openResultDetails = async (resultId: string): Promise<void> => {
    setBusy(true);
    try {
      const details = await resultsApi.get(resultId);
      setSelected(details);
      openRoute({ kind: "result-details", resultId });
    } catch {
      setError("Не удалось открыть результат. Попробуйте позже.");
    } finally {
      setBusy(false);
    }
  };

  const buildPdfUrl = (resultId: string, disposition: "inline" | "attachment"): string =>
    `${baseUrl}/patient/results/${encodeURIComponent(resultId)}/pdf?disposition=${disposition}`;

  const sharePdf = async (resultId: string): Promise<void> => {
    try {
      const response = await fetch(buildPdfUrl(resultId, "attachment"), { credentials: "include" });
      if (!response.ok) throw new Error("pdf");
      const blob = await response.blob();
      const file = new File([blob], `result-${resultId}.pdf`, { type: "application/pdf" });
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: `Результат №${resultId}`, text: "PDF файл результата анализа" });
        return;
      }
      setInfoMessage("На этом устройстве отправка PDF-файла недоступна. Откройте PDF и используйте системное меню браузера.");
    } catch {
      setInfoMessage("На этом устройстве отправка PDF-файла недоступна. Откройте PDF и используйте системное меню браузера.");
    }
  };

  const renderIndicators = (details: PatientResultDetails): JSX.Element => {
    const indicators = buildPatientIndicators(details);
    if (indicators.length === 0) {
      return <p className="muted">{miniAppContentConfig.resultDetails.notAvailable}</p>;
    }
    return (
      <div className="lab-table">
        <div className="lab-table__head">
          <span>Показатель</span>
          <span>Значение</span>
        </div>
        {indicators.map((indicator) => (
          <div className="lab-table__row" key={indicator.id}>
            <span>{indicator.label}</span>
            <strong>{indicator.valueText}</strong>
          </div>
        ))}
      </div>
    );
  };

  const renderServiceNode = (node: ServiceTreeNode, depth = 0): JSX.Element => {
    const hasChildren = Boolean(node.children?.length);
    const expanded = expandedNodes.has(node.id);

    return (
      <div key={node.id} className="service-node" style={{ marginLeft: `${depth * 14}px` }}>
        <button
          type="button"
          className="service-node__row"
          onClick={() => {
            if (hasChildren) {
              setExpandedNodes((prev) => {
                const next = new Set(prev);
                if (next.has(node.id)) {
                  next.delete(node.id);
                } else {
                  next.add(node.id);
                }
                return next;
              });
            }
          }}
        >
          <span>{node.name}</span>
          {typeof node.priceRub === "number" ? <strong>{node.priceRub} ₽</strong> : null}
          {hasChildren ? <span className="service-node__toggle">{expanded ? "▾" : "▸"}</span> : null}
        </button>
        {hasChildren && expanded ? node.children!.map((child) => renderServiceNode(child, depth + 1)) : null}
      </div>
    );
  };

  const filteredCategories = miniAppContentConfig.services.categories
    .map((category) => filterCategory(category, servicesQuery))
    .filter((category): category is ServiceCategory => Boolean(category));

  const selectedCategory =
    filteredCategories.find((category) => category.id === selectedCategoryId) ?? filteredCategories[0] ?? null;

  return (
    <MaxUI>
      <main className="mobile-app">
        {loading ? <p className="status">Загрузка...</p> : null}

        {!loading && !session ? (
          <section className="login-screen">
            <div className="login-brand">
              <img src={asset("logo-smart.svg")} alt="СМАРТ" />
              <p>{miniAppContentConfig.clinicSubtitle}</p>
            </div>

            <div className="card login-card">
              <h1>{miniAppContentConfig.login.title}</h1>
              <p className="muted">{miniAppContentConfig.login.subtitle}</p>
              <input
                className="input"
                placeholder={miniAppContentConfig.login.loginPlaceholder}
                value={login}
                onChange={(event) => setLogin(event.target.value)}
              />
              <div className="password-field">
                <input
                  className="input"
                  type={passwordVisible ? "text" : "password"}
                  placeholder={miniAppContentConfig.login.passwordPlaceholder}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
                <button
                  type="button"
                  className="icon-btn password-field__toggle"
                  onClick={() => setPasswordVisible((prev) => !prev)}
                  aria-label={passwordVisible ? miniAppContentConfig.login.hidePasswordLabel : miniAppContentConfig.login.showPasswordLabel}
                >
                  <img src={asset(passwordVisible ? "icon-eye-off.svg" : "icon-eye.svg")} alt="" aria-hidden="true" />
                </button>
              </div>
              <button type="button" className="primary-btn" disabled={busy} onClick={() => void handleLoginSubmit()}>
                {miniAppContentConfig.login.submitLabel}
              </button>
            </div>

            <div className="card help-card">
              <div>
                <p className="help-card__eyebrow">Нужна помощь?</p>
                <p>Позвоните администратору</p>
                <span>{miniAppContentConfig.clinicHours}</span>
              </div>
              <a href={`tel:${miniAppContentConfig.clinicPhone.replace(/[^\d+]/g, "")}`} className="phone-link">{miniAppContentConfig.clinicPhone}</a>
            </div>
          </section>
        ) : null}

        {!loading && session ? (
          <>
            {route.kind !== "tab" ? (
              <header className="top-bar">
                <button type="button" className="icon-btn back-btn" onClick={goBack} aria-label="Назад">‹</button>
                <h2>
                  {route.kind === "result-details"
                    ? `Исследование №${route.resultId}`
                    : `${miniAppContentConfig.pdfViewer.titlePrefix}${route.resultId}`}
                </h2>
              </header>
            ) : null}

            {route.kind === "tab" && route.tab === "home" ? (
              <section>
                <header className="home-header">
                  <div>
                    <p className="eyebrow">{miniAppContentConfig.home.greetingPrefix}</p>
                    <h1>{greetingName}!</h1>
                  </div>
                  <img src={asset("logo-smart.svg")} alt="СМАРТ" />
                </header>

                <article className={`card profile-card ${profileExpanded ? "profile-card--expanded" : ""}`} data-testid="patient-card">
                  <button type="button" className="profile-card__summary" onClick={() => setProfileExpanded((prev) => !prev)}>
                    <span className="avatar">
                      {session.avatar_url ? <img src={session.avatar_url} alt="Аватар" /> : <span>{initials(session.patient_name)}</span>}
                    </span>
                    <span className="profile-card__identity">
                      <strong>{session.patient_name}</strong>
                      <small>Дата рождения: {birthDate}</small>
                    </span>
                    <span className="profile-card__chevron" aria-hidden="true">{profileExpanded ? "⌃" : "⌄"}</span>
                  </button>
                  {profileExpanded ? (
                    <div className="profile-card__details">
                      <dl>
                        <div><dt>ФИО</dt><dd>{session.patient_name}</dd></div>
                        <div><dt>Дата рождения</dt><dd>{birthDate}</dd></div>
                        <div><dt>Телефон</dt><dd>{normalizeProfileField(phone)}</dd></div>
                        <div><dt>Email</dt><dd>{normalizeProfileField(email)}</dd></div>
                      </dl>
                      <p className="muted">{miniAppContentConfig.home.profileHint}</p>
                    </div>
                  ) : null}
                </article>

                <div className="section-grid">
                  {miniAppContentConfig.home.sections.map((item) => (
                    <button key={item.id} type="button" className={`card section-card section-card--${item.tone}`} onClick={() => openTab(item.id)}>
                      <img src={sectionAssetById[item.id]} alt="" aria-hidden="true" />
                      <div>
                        <h4>{item.title}</h4>
                        <p>{item.description}</p>
                      </div>
                      <span aria-hidden="true">›</span>
                    </button>
                  ))}
                </div>
              </section>
            ) : null}

            {route.kind === "tab" && route.tab === "results" ? (
              <section>
                <h2>{miniAppContentConfig.results.title}</h2>
                <p className="muted">{miniAppContentConfig.results.subtitle}</p>
                {results.length === 0 ? <p>{miniAppContentConfig.results.emptyLabel}</p> : null}
                <div className="results-list">
                  {results.map((item) => (
                    <button key={item.result_id} type="button" className="card result-card" onClick={() => void openResultDetails(item.result_id)}>
                      <span className="result-card__icon"><img src={asset("icon-analyses.svg")} alt="" aria-hidden="true" /></span>
                      <div className="result-card__body">
                        <p className="result-title">Исследование №{item.result_id}</p>
                        <p className="result-meta">{item.date ?? "Дата не указана"}</p>
                        {item.lab_name ? <p className="muted">{item.lab_name}</p> : <p className="muted">Лаборатория не указана</p>}
                      </div>
                      <span className={`status-pill status-pill--${statusTone(item.status)}`}>{item.status || miniAppContentConfig.results.readyLabel}</span>
                      <span className="result-card__arrow" aria-hidden="true">›</span>
                    </button>
                  ))}
                </div>
              </section>
            ) : null}

            {route.kind === "result-details" && selected ? (
              <section>
                <article className="card details-summary">
                  <div>
                    <p className="eyebrow">Исследование</p>
                    <h3>№{selected.result_id}</h3>
                  </div>
                  <span className={`status-pill status-pill--${statusTone(selected.status)}`}>{selected.status}</span>
                  <dl>
                    <div><dt>Дата</dt><dd>{selected.date ?? "—"}</dd></div>
                    <div><dt>Лаборатория</dt><dd>{selected.lab_name ?? "—"}</dd></div>
                  </dl>
                </article>

                <article className="card indicators-card">
                  <h3>Показатели</h3>
                  {renderIndicators(selected)}
                  <button
                    type="button"
                    className="primary-btn"
                    disabled={!selected.has_pdf}
                    onClick={() => openRoute({ kind: "pdf", resultId: selected.result_id })}
                  >
                    {miniAppContentConfig.resultDetails.openPdfLabel}
                  </button>
                </article>
              </section>
            ) : null}

            {route.kind === "pdf" ? (
              <section className="pdf-screen">
                <div className="pdf-frame-wrap card">
                  <iframe title="PDF документ" src={buildPdfUrl(route.resultId, "inline")} className="pdf-frame" />
                </div>
                <div className="pdf-actions">
                  <button type="button" onClick={() => void sharePdf(route.resultId)}>
                    <span aria-hidden="true">↗</span>
                    {miniAppContentConfig.pdfViewer.share}
                  </button>
                </div>
              </section>
            ) : null}

            {route.kind === "tab" && route.tab === "appointment" ? (
              <section>
                <h2>{miniAppContentConfig.appointment.title}</h2>
                <p className="muted">{miniAppContentConfig.appointment.subtitle}</p>
                <p className="foundation-note">{miniAppContentConfig.appointment.foundationNote}</p>
                {miniAppContentConfig.appointment.doctors.map((doctor) => (
                  <article className="card doctor-card" key={doctor.id}>
                    <div className="doctor-avatar"><img src={asset("icon-appointment.svg")} alt="" aria-hidden="true" /></div>
                    <div>
                      <h3>{doctor.fullName}</h3>
                      <p>{doctor.specialty}</p>
                      <p className="muted">{doctor.about}</p>
                      {doctor.nextSlots.map((slots) => (
                        <p key={slots.dayLabel}><strong>{slots.dayLabel}:</strong> {slots.times.join(" · ")}</p>
                      ))}
                    </div>
                  </article>
                ))}
              </section>
            ) : null}

            {route.kind === "tab" && route.tab === "loyalty" ? (
              <section>
                <h2>{miniAppContentConfig.loyalty.title}</h2>
                <p className="muted">{miniAppContentConfig.loyalty.subtitle}</p>
                <p className="foundation-note">{miniAppContentConfig.loyalty.foundationNote}</p>
                <div className="split-grid">
                  <article className="card"><p>Бонусные рубли</p><h3>{miniAppContentConfig.loyalty.bonusRub.toLocaleString("ru-RU")} ₽</h3></article>
                  <article className="card"><p>Текущая скидка</p><h3>{miniAppContentConfig.loyalty.discountPercent}%</h3></article>
                </div>
                <article className="card">
                  <p>До следующего уровня: 10%</p>
                  <div className="progress"><span style={{ width: `${miniAppContentConfig.loyalty.progressPercent}%` }} /></div>
                </article>
                <div className="split-grid">
                  {miniAppContentConfig.loyalty.promos.map((promo) => (
                    <article className={`card promo-card promo-card--${promo.accent}`} key={promo.id}>
                      <p>{promo.subtitle}</p>
                      <h3>{promo.title}</h3>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}

            {route.kind === "tab" && route.tab === "services" ? (
              <section>
                <h2>{miniAppContentConfig.services.title}</h2>
                <p className="muted">{miniAppContentConfig.services.subtitle}</p>
                <p className="foundation-note">{miniAppContentConfig.services.foundationNote}</p>
                <input
                  className="input"
                  placeholder={miniAppContentConfig.services.searchPlaceholder}
                  value={servicesQuery}
                  onChange={(event) => setServicesQuery(event.target.value)}
                />
                <p className="muted">{miniAppContentConfig.services.searchHint}</p>
                <div className="category-grid">
                  {filteredCategories.map((category) => (
                    <button
                      key={category.id}
                      type="button"
                      className={`card category-card ${selectedCategory?.id === category.id ? "category-card--active" : ""}`}
                      onClick={() => setSelectedCategoryId(category.id)}
                    >
                      <h4>{category.name}</h4>
                      <p>{category.servicesCount} услуг</p>
                    </button>
                  ))}
                </div>
                {selectedCategory ? <article className="card">{selectedCategory.tree.map((node) => renderServiceNode(node))}</article> : <p>Ничего не найдено.</p>}
              </section>
            ) : null}

            <nav className="bottom-nav">
              {miniAppContentConfig.navigation.map((item) => (
                <button
                  key={item.tab}
                  type="button"
                  className={route.kind === "tab" && route.tab === item.tab ? "active" : ""}
                  onClick={() => openTab(item.tab)}
                >
                  <img src={tabIconById[item.tab]} alt="" aria-hidden="true" />
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>
          </>
        ) : null}

        {busy ? <p className="status">Подождите...</p> : null}
        {error ? <p className="status status--error">{error}</p> : null}
        {infoMessage ? <p className="status">{infoMessage}</p> : null}
      </main>
    </MaxUI>
  );
}
