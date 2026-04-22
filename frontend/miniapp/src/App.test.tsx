import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

describe("App patient mini app", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    (globalThis as { fetch: typeof fetch }).fetch = vi.fn();
    vi.spyOn(window, "open").mockReturnValue(null);
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
    expect(screen.queryByText("Мои записи", { selector: "button" })).not.toBeInTheDocument();
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
    await waitFor(() => expect(screen.getByLabelText("Открыть PDF")).toBeInTheDocument());
    expect(screen.getByLabelText("Открыть PDF")).toBeDisabled();
    expect(screen.getByLabelText("Скачать PDF")).toBeDisabled();
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
    await waitFor(() => expect(screen.getByLabelText("Скачать PDF")).toBeInTheDocument());
    fireEvent.click(screen.getByLabelText("Скачать PDF"));
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
            indicators: [{ parameter_name: "K", parameter_value: "4.2", measurement_unit: "ммоль/л" }],
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
    fireEvent.click(screen.getByLabelText("Открыть"));
    await waitFor(() => expect(screen.getByText("Калий (К+): 4.2 ммоль/л")).toBeInTheDocument());
  });

  it("открывает details по клику на всю карточку результата", async () => {
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
            services: [],
            sections: [],
            indicators: [],
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
    fireEvent.click(screen.getByText("Результат №r1").closest("section") as HTMLElement);
    await waitFor(() => expect(screen.getByText("Карточка результата")).toBeInTheDocument());
  });
});
