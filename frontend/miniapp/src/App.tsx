import { useEffect, useMemo, useState } from "react";
import { MaxUI } from "@maxhub/max-ui";
import { ApiClient, ApiError } from "./api/client";
import { PatientResultDetails, PatientResultListItem, ResultsApi } from "./api/results";
import { AuthApi, PatientSession } from "./api/auth";
import { buildPatientIndicators } from "./utils/patientResults";
import { MainTab, miniAppContentConfig, ServiceCategory, ServiceTreeNode } from "./ui/contentConfig";
import { AppointmentSlotDto, LoyaltyDto, PortalApi, ServiceCategoryDto, ServiceDto } from "./api/portal";

type Route =
  | { kind: "tab"; tab: MainTab }
  | { kind: "result-details"; resultId: string }
  | { kind: "pdf"; resultId: string };

type ExtendedSession = PatientSession & {
  patient_phone?: string | null;
  birth_date?: string | null;
  phone?: string | null;
  email?: string | null;
  avatar_url?: string | null;
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

export function App(): JSX.Element {
  const baseUrl = resolvePatientApiBaseUrl();
  const client = useMemo(() => new ApiClient({ baseUrl }), [baseUrl]);
  const authApi = useMemo(() => new AuthApi(client), [client]);
  const resultsApi = useMemo(() => new ResultsApi(client), [client]);
  const portalApi = useMemo(() => new PortalApi(client), [client]);

  const [session, setSession] = useState<ExtendedSession | null>(null);
  const [results, setResults] = useState<PatientResultListItem[]>([]);
  const [selected, setSelected] = useState<PatientResultDetails | null>(null);
  const [route, setRoute] = useState<Route>({ kind: "tab", tab: "home" });
  const [history, setHistory] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultsError, setResultsError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [loyalty, setLoyalty] = useState<LoyaltyDto | null>(null);
  const [serviceCategories, setServiceCategories] = useState<ServiceCategoryDto[]>([]);
  const [serviceItems, setServiceItems] = useState<ServiceDto[]>([]);
  const [scheduleSlots, setScheduleSlots] = useState<AppointmentSlotDto[]>([]);

  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [passwordVisible, setPasswordVisible] = useState(false);

  const [servicesQuery, setServicesQuery] = useState("");
  const [selectedCategoryId, setSelectedCategoryId] = useState(miniAppContentConfig.services.categories[0]?.id ?? "");
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [patientCardExpanded, setPatientCardExpanded] = useState(false);

  useEffect(() => {
    const autoLoginToken = new URLSearchParams(window.location.search).get("auto_login_token");
    const resolveSession = autoLoginToken ? authApi.autoLoginByToken(autoLoginToken) : authApi.me();
    resolveSession
      .then((currentSession) => {
        setSession(currentSession as ExtendedSession);
        if (autoLoginToken) {
          const nextUrl = new URL(window.location.href);
          nextUrl.searchParams.delete("auto_login_token");
          window.history.replaceState({}, "", nextUrl.toString());
        }
        return loadResults();
      })
      .catch(() => setSession(null))
      .finally(() => setLoading(false));
  }, [authApi, resultsApi]);

  const patientName = session?.patient_name ?? "";
  const greetingName = patientName.split(" ").slice(1, 3).join(" ") || patientName || "пациент";
  const phone = session?.patient_phone ?? session?.phone ?? miniAppContentConfig.clinicPhone;
  const email = session?.email ?? "—";
  const birthDate =
    session?.birth_date && !String(session.birth_date).toLowerCase().includes("pn-") ? session.birth_date : "не указана";

  const loadResults = async (): Promise<void> => {
    try {
      const items = await resultsApi.list();
      setResults(items);
      setResultsError(null);
    } catch (err: unknown) {
      setResults([]);
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        setResultsError("Сессия истекла. Войдите заново.");
      } else {
        setResultsError("Не удалось загрузить результаты. Попробуйте позже.");
      }
    }
  };

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
    if (tab === "loyalty") { void portalApi.loyalty().then(setLoyalty).catch(() => setInfoMessage("Не удалось загрузить баланс.")); }
    if (tab === "services") {
      void portalApi.serviceCategories().then(setServiceCategories).catch(() => setInfoMessage("Не удалось загрузить категории услуг."));
      void portalApi.services().then(setServiceItems).catch(() => setInfoMessage("Не удалось загрузить услуги."));
    }
    if (tab === "appointment") { void portalApi.schedule().then(setScheduleSlots).catch(() => setInfoMessage("Не удалось загрузить расписание.")); }
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
      setError(null);
      await loadResults();
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

  const savePdf = (_resultId: string): void => {};

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
          <section className="login-screen-wrap">
            <div className="login-branding card">
              <img
                src="/assets/logo-smart.svg"
                alt="СМАРТ"
                className="login-branding__logo"
                onError={(event) => {
                  event.currentTarget.style.display = "none";
                }}
              />
              <p className="login-branding__subtitle">{miniAppContentConfig.login.subtitle}</p>
            </div>

            <div className="login-screen card login-screen--aligned">
              <h2>{miniAppContentConfig.login.title}</h2>
              <input
                className="input input--login"
                placeholder="Введите сюда свой логин"
                value={login}
                onChange={(event) => setLogin(event.target.value)}
              />
              <div className="password-row">
                <input
                  className="input input--login"
                  type={passwordVisible ? "text" : "password"}
                  placeholder="Введите сюда свой пароль"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
                <button
                  type="button"
                  className="ghost ghost--icon"
                  aria-label={passwordVisible ? "Скрыть пароль" : "Показать пароль"}
                  onClick={() => setPasswordVisible((prev) => !prev)}
                >
                  <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                    {passwordVisible ? (
                      <>
                        <path d="M3 3l18 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                        <path d="M10.6 6.7a10.9 10.9 0 0 1 1.4-.1c5.2 0 9.3 3.7 10 5.4-.2.5-.7 1.3-1.5 2.1" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M14.1 14.1a3 3 0 0 1-4.2-4.2" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M6.1 9.7C4.4 11 3.3 12.7 3 13c.9 1.9 5 5.4 9 5.4 1.6 0 3-.4 4.3-1" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                      </>
                    ) : (
                      <>
                        <path d="M2.8 12c1-2 5-5.6 9.2-5.6s8.2 3.6 9.2 5.6c-1 2-5 5.6-9.2 5.6S3.8 14 2.8 12z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.8" />
                      </>
                    )}
                  </svg>
                </button>
              </div>

              <button type="button" className="primary-btn" disabled={busy} onClick={() => void handleLoginSubmit()}>
                {miniAppContentConfig.login.submitLabel}
              </button>

            </div>

            <div className="support-card card">
              <div className="support-card__icon" aria-hidden="true">📞</div>
              <div>
                <p className="help-text">Нужна помощь?<br />{miniAppContentConfig.clinicHours}</p>
                <a href={`tel:${miniAppContentConfig.clinicPhone.replace(/[^\d+]/g, "")}`} className="phone-link">
                  {miniAppContentConfig.clinicPhone}
                </a>
              </div>
            </div>
            <p className="login-footer">© 2024 Медицинский центр СМАРТ</p>
          </section>
        ) : null}

        {!loading && session ? (
          <>
            {route.kind !== "tab" ? (
              <header className="top-bar">
                <button type="button" className="back-btn" onClick={goBack} aria-label="Назад">←</button>
                <h2>
                  {route.kind === "result-details"
                    ? `Исследование №${route.resultId}`
                    : `${miniAppContentConfig.pdfViewer.titlePrefix}${route.resultId}`}
                </h2>
              </header>
            ) : null}

            {route.kind === "tab" && route.tab === "home" ? (
              <section>
                <article className="card profile-card" data-testid="patient-card">
                  <button type="button" className="profile-card__header" onClick={() => setPatientCardExpanded((prev) => !prev)}>
                    <img className="avatar" src={session.avatar_url || "/assets/avatar-placeholder.svg"} alt="Аватар пациента" />
                    <div>
                      <h2>{session.patient_name}</h2>
                      <p><strong>Дата рождения:</strong> {birthDate}</p>
                    </div>
                    <span className="profile-card__chevron">{patientCardExpanded ? "▴" : "▾"}</span>
                  </button>
                  {patientCardExpanded ? (
                    <div>
                      <p><strong>Телефон:</strong> {phone}</p>
                      <p><strong>Email:</strong> {email}</p>
                      <p className="muted">{miniAppContentConfig.home.profileHint}</p>
                    </div>
                  ) : null}
                </article>
                <h3>{miniAppContentConfig.home.greetingPrefix}, {greetingName}!</h3>
                <div className="section-grid">
                  {miniAppContentConfig.home.sections.map((item) => (
                    <button key={item.id} type="button" className={`card section-card section-card--${item.tone}`} data-testid={`home-tile-${item.id}`} onClick={() => openTab(item.id)}>
                      <div>
                        <h4>{item.title}</h4>
                        <p>{item.description}</p>
                      </div>
                      <img src={`/assets/${item.iconAsset}`} className="section-icon" alt={item.title} />
                    </button>
                  ))}
                </div>
              </section>
            ) : null}

            {route.kind === "tab" && route.tab === "results" ? (
              <section>
                <h2>{miniAppContentConfig.results.title}</h2>
                <p className="muted">{miniAppContentConfig.results.subtitle}</p>
                {resultsError ? <p className="status status--error">{resultsError}</p> : null}
                {results.length === 0 ? <p>{miniAppContentConfig.results.emptyLabel}</p> : null}
                <div className="results-list">
                  {results.map((item) => (
                    <button key={item.result_id} type="button" className="card result-card" onClick={() => void openResultDetails(item.result_id)}>
                      <div>
                        <p className="result-title">Результат №{item.result_id}</p>
                        <p>{item.date ?? "—"}</p>
                        {item.lab_name ? <p className="muted">{item.lab_name}</p> : null}
                        <p className="status-pill">{item.status || miniAppContentConfig.results.readyLabel}</p>
                      </div>
                      <span>›</span>
                    </button>
                  ))}
                </div>
              </section>
            ) : null}

            {route.kind === "result-details" && selected ? (
              <section>
                <article className="card details-card">
                  <p><strong>Исследование №{selected.result_id}</strong></p>
                  <p>Дата: {selected.date ?? "—"}</p>
                  <p>Статус: {selected.status}</p>
                  <p>Лаборатория: {selected.lab_name ?? "—"}</p>
                  <div className="indicator-list">
                    {buildPatientIndicators(selected).map((indicator) => (
                      <div key={indicator.id} className="indicator-item">
                        <p className="indicator-item__label">{indicator.label}</p>
                        <p className="indicator-item__value">{indicator.valueText}</p>
                      </div>
                    ))}
                    {buildPatientIndicators(selected).length === 0 ? <p>{miniAppContentConfig.resultDetails.notAvailable}</p> : null}
                  </div>
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
                  <button type="button" onClick={() => void sharePdf(route.resultId)}>{miniAppContentConfig.pdfViewer.share}</button>
                </div>
              </section>
            ) : null}

            {route.kind === "tab" && route.tab === "appointment" ? (
              <section>
                <h2>{miniAppContentConfig.appointment.title}</h2>
                <p className="muted">{miniAppContentConfig.appointment.subtitle}</p>
                <p className="foundation-note">{miniAppContentConfig.appointment.foundationNote}</p>
                {scheduleSlots.length === 0 ? <p className="foundation-note">Нет доступных слотов.</p> : scheduleSlots.map((slot) => (
                  <article className="card doctor-card" key={slot.schedule_id}>
                    <div className="doctor-avatar">🩺</div>
                    <div>
                      <h3>{slot.doctor_name}</h3>
                      <p>{slot.profession ?? "Специалист"}</p>
                      <p className="muted">{slot.clinic_name ?? "Клиника"}{slot.room ? ` · Кабинет ${slot.room}` : ""}</p>
                      <p><strong>{slot.date}:</strong> {slot.time_start}</p>
                    </div>
                  </article>
                ))}
              </section>
            ) : null}

            {route.kind === "tab" && route.tab === "loyalty" ? (
              <section>
                <h2>{miniAppContentConfig.loyalty.title}</h2>
                <p className="muted">{miniAppContentConfig.loyalty.subtitle}</p>
                {!loyalty ? <p className="foundation-note">Загрузка баланса...</p> : <>
                <div className="split-grid">
                  <article className="card"><p>Баланс</p><h3>{loyalty.balance.toLocaleString("ru-RU")} ₽</h3></article>
                  <article className="card"><p>Бонусные рубли</p><h3>{loyalty.bonus_funds.toLocaleString("ru-RU")} ₽</h3></article>
                </div>
                <article className="card">
                  <p>Средства пациента: {loyalty.patient_funds.toLocaleString("ru-RU")} ₽</p>
                  <p>Задолженность: {loyalty.patient_debt.toLocaleString("ru-RU")} ₽</p>
                </article></>}
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
                
                <input
                  className="input"
                  placeholder={miniAppContentConfig.services.searchPlaceholder}
                  value={servicesQuery}
                  onChange={(event) => setServicesQuery(event.target.value)}
                />
                <p className="muted">{miniAppContentConfig.services.searchHint}</p>
                <div className="category-grid">
                  {(serviceCategories.length > 0 ? serviceCategories.map((c) => ({id:c.id,name:c.title,servicesCount:c.services_count,tree:[]} as unknown as ServiceCategory)) : filteredCategories).map((category) => (
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
                <article className="card">{(serviceItems.filter((item) => !selectedCategory || item.category_id === selectedCategory.id).filter((item)=> item.title.toLowerCase().includes(servicesQuery.toLowerCase()))).map((item) => <p key={item.service_id}>{item.title}{typeof item.price === "number" ? ` — ${item.price} ₽` : ""}</p>)}</article>
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
                  {item.label}
                </button>
              ))}
            </nav>
          </>
        ) : null}

        {busy ? <p className="status">Подождите...</p> : null}
        {!session && error ? <p className="status status--error">{error}</p> : null}
        {infoMessage ? <p className="status">{infoMessage}</p> : null}
      </main>
    </MaxUI>
  );
}
