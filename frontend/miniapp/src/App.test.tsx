import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

describe("App patient mini app", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    (globalThis as { fetch: typeof fetch }).fetch = vi.fn();
  });

  it("показывает экран входа при отсутствии сессии", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response("unauthorized", { status: 401 }));
    render(<App />);
    await waitFor(() => expect(screen.getByText("Вход")).toBeInTheDocument());
  });

  it("логин и переход к списку результатов", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response("unauthorized", { status: 401 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            session_id: "s1",
            patient_name: "Тест",
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
    expect(screen.getByText("Поддержка")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Результаты анализов"));
    await waitFor(() => expect(screen.getByText("Результат №r1")).toBeInTheDocument());
    expect(screen.queryByText("Очень длинный список услуг")).not.toBeInTheDocument();
  });

  it("скрывает активные PDF-действия если has_pdf=false", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            session_id: "s1",
            patient_name: "Тест",
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
              status: "В обработке",
              has_pdf: false,
              lab_name: "Lab",
              clinic_name: "Clinic",
              short_services_summary: "ОАК",
            },
          ]),
          { status: 200 },
        ),
      );

    render(<App />);
    await waitFor(() => expect(screen.getByText("Результаты анализов")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Результаты анализов"));
    await waitFor(() => expect(screen.getByText("Открыть PDF")).toBeInTheDocument());
    expect(screen.getByText("Открыть PDF")).toBeDisabled();
    expect(screen.getByText("Скачать PDF")).toBeDisabled();
  });

  it("показывает человекочитаемую ошибку PDF вместо сырого payload", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            session_id: "s1",
            patient_name: "Тест",
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
              short_services_summary: "ОАК",
            },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response('{"message":"raw backend json"}', { status: 502 }));

    render(<App />);
    await waitFor(() => expect(screen.getByText("Результаты анализов")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Результаты анализов"));
    await waitFor(() => expect(screen.getByText("Скачать PDF")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Скачать PDF"));
    await waitFor(() => expect(screen.getByText("Сервис временно недоступен. Попробуйте позже.")).toBeInTheDocument());
    expect(screen.queryByText(/raw backend json/i)).not.toBeInTheDocument();
  });

  it("в details показывает реальные показатели в формате Название: значение единица", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            session_id: "s1",
            patient_name: "Тест",
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
              short_services_summary: "ОАК",
            },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            result_id: "r1",
            title: "ОАК",
            date: "2026-01-02",
            status: "Готов",
            has_pdf: true,
            lab_name: "Lab",
            clinic_name: "Clinic",
            services: ["K • Калий (К+)"],
            sections: [],
            indicators: [{ parameter_name: "K", value: "4.2", unit: "ммоль/л" }],
            pdf_open_url: "/patient/results/r1/pdf",
            pdf_download_url: "/patient/results/r1/pdf",
          }),
          { status: 200 },
        ),
      );

    render(<App />);
    await waitFor(() => expect(screen.getByText("Результаты анализов")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Результаты анализов"));
    await waitFor(() => expect(screen.getByText("Результат №r1")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Открыть"));
    await waitFor(() => expect(screen.getByText("Калий (К+): 4.2 ммоль/л")).toBeInTheDocument());
  });
});
