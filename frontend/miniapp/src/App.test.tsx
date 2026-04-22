import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

function stubAuthorizedBoot(hasPdf = true): void {
  vi.mocked(fetch)
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          session_id: "s1",
          patient_name: "Иванов Иван Иванович",
          patient_number: "p1",
          created_at: "2026-01-01",
          expires_at: "2026-12-01",
          last_refresh_at: "2026-01-01",
          auth_type: "login",
        }),
        { status: 200 },
      ),
    )
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify([
          {
            result_id: "r1",
            title: "ОАК",
            date: "2026-01-02",
            status: "Готов",
            has_pdf: hasPdf,
            lab_name: "Lab",
            clinic_name: "Clinic",
            short_services_summary: "ОАК",
          },
        ]),
        { status: 200 },
      ),
    );
}

describe("App patient mini app", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    (globalThis as { fetch: typeof fetch }).fetch = vi.fn();
    vi.spyOn(window, "open").mockReturnValue(null);
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn().mockReturnValue("blob:pdf"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(),
    });
    Object.defineProperty(navigator, "share", {
      configurable: true,
      writable: true,
      value: undefined,
    });
    Object.defineProperty(navigator, "canShare", {
      configurable: true,
      writable: true,
      value: undefined,
    });
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      writable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  it("показывает экран входа при отсутствии сессии", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response("unauthorized", { status: 401 }));
    render(<App />);
    await waitFor(() => expect(screen.getByText("Вход")).toBeInTheDocument());
  });

  it("логин и переход к списку результатов с главным CTA", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response("unauthorized", { status: 401 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            session_id: "s1",
            patient_name: "Иванов Иван Иванович",
            patient_number: "p1",
            created_at: "2026-01-01",
            expires_at: "2026-12-01",
            last_refresh_at: "2026-01-01",
            auth_type: "login",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            {
              result_id: "r1",
              title: "ОАК",
              date: "2026-01-02",
              status: "Готов",
              has_pdf: true,
              lab_name: "Lab",
              clinic_name: "Clinic",
              short_services_summary: "Очень длинный список услуг",
            },
          ]),
          { status: 200 },
        ),
      );

    render(<App />);
    await waitFor(() => expect(screen.getByText("Вход")).toBeInTheDocument());
    fireEvent.change(screen.getByPlaceholderText("Логин"), { target: { value: "demo" } });
    fireEvent.change(screen.getByPlaceholderText("Пароль"), { target: { value: "secret" } });
    fireEvent.click(screen.getByText("Войти"));

    await waitFor(() => expect(screen.getByText("Результаты анализов")).toBeInTheDocument());
    expect(screen.getByText("Здравствуйте, Иван Иванович!")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Результаты анализов"));
    await waitFor(() => expect(screen.getByText("Результат №r1")).toBeInTheDocument());
  });

  it("открывает управляемый PDF viewer с top/bottom action bar и кнопкой Назад", async () => {
    stubAuthorizedBoot(true);

    render(<App />);
    await waitFor(() => expect(screen.getByText("Результаты анализов")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Результаты анализов"));
    await waitFor(() => expect(screen.getByLabelText("Открыть PDF")).toBeInTheDocument());
    fireEvent.click(screen.getByLabelText("Открыть PDF"));

    expect(screen.getByLabelText("Экран просмотра PDF")).toBeInTheDocument();
    expect(screen.getByText("Назад", { selector: "button" })).toBeInTheDocument();
    expect(screen.getByText("Выйти", { selector: "button" })).toBeInTheDocument();
    expect(screen.getByText("Сохранить", { selector: "button" })).toBeInTheDocument();
    expect(screen.getByText("Поделиться", { selector: "button" })).toBeInTheDocument();
    expect(screen.getByText("Отправить в MAX", { selector: "button" })).toBeInTheDocument();

    fireEvent.click(screen.getByText("Назад", { selector: "button" }));
    await waitFor(() => expect(screen.getByText("Результат №r1")).toBeInTheDocument());
  });

  it("кнопка Выйти в PDF viewer вызывает logout flow и возвращает на экран логина", async () => {
    stubAuthorizedBoot(true);
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ success: true }), { status: 200 }));

    render(<App />);
    await waitFor(() => expect(screen.getByText("Результаты анализов")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Результаты анализов"));
    await waitFor(() => expect(screen.getByLabelText("Открыть PDF")).toBeInTheDocument());
    fireEvent.click(screen.getByLabelText("Открыть PDF"));
    fireEvent.click(screen.getByText("Выйти", { selector: "button" }));

    await waitFor(() => expect(screen.getByText("Вход")).toBeInTheDocument());
  });

  it("делает graceful fallback в Share при отсутствии системного share API", async () => {
    stubAuthorizedBoot(true);
    vi.mocked(fetch).mockResolvedValueOnce(new Response(new Blob(["pdf"], { type: "application/pdf" }), { status: 200 }));

    render(<App />);
    await waitFor(() => expect(screen.getByText("Результаты анализов")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Результаты анализов"));
    await waitFor(() => expect(screen.getByLabelText("Открыть PDF")).toBeInTheDocument());
    fireEvent.click(screen.getByLabelText("Открыть PDF"));
    fireEvent.click(screen.getByText("Поделиться", { selector: "button" }));

    await waitFor(() => {
      expect(screen.getByText("Системный share недоступен. Ссылка на PDF скопирована в буфер обмена.")).toBeInTheDocument();
    });
  });

  it("скрывает активные PDF-действия если has_pdf=false", async () => {
    stubAuthorizedBoot(false);

    render(<App />);
    await waitFor(() => expect(screen.getByText("Результаты анализов")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Результаты анализов"));
    await waitFor(() => expect(screen.getByLabelText("Открыть PDF")).toBeInTheDocument());
    expect(screen.getByLabelText("Открыть PDF")).toBeDisabled();
    expect(screen.getByLabelText("Скачать PDF")).toBeDisabled();
  });
});
