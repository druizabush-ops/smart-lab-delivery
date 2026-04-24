import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

function mockSessionResponse(): Response {
  return new Response(
    JSON.stringify({
      session_id: "s1",
      patient_name: "Иванов Иван Иванович",
      patient_number: "15.05.1985",
      created_at: "2026-01-01",
      expires_at: "2026-12-01",
      last_refresh_at: "2026-01-01",
      auth_type: "login",
      patient_phone: "+7 (999) 123-45-67",
      email: "ivanov@mail.ru",
    }),
    { status: 200 },
  );
}

function mockResultListResponse(): Response {
  return new Response(
    JSON.stringify([
      {
        result_id: "125487",
        title: "Тест",
        date: "2026-03-29",
        status: "Готово",
        has_pdf: true,
        lab_name: "Гемотест",
        clinic_name: "СМАРТ",
        short_services_summary: "Скрыть",
      },
    ]),
    { status: 200 },
  );
}

function mockResultDetailsResponse(): Response {
  return new Response(
    JSON.stringify({
      result_id: "125487",
      title: "Тест",
      date: "2026-03-29",
      status: "Готово",
      has_pdf: true,
      lab_name: "Гемотест",
      clinic_name: "СМАРТ",
      services: ["K • Калий (К+)", "PRL • Пролактин"],
      sections: [],
      indicators: [
        { parameter_name: "K", parameter_value: "4.2", measurement_unit: "ммоль/л" },
        { parameter_name: "PRL", parameter_value: "53.8 ++", measurement_unit: "нг/мл" },
      ],
      pdf_open_url: "/patient/results/125487/pdf",
      pdf_download_url: "/patient/results/125487/pdf",
    }),
    { status: 200 },
  );
}

describe("mini app redesign", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    (globalThis as { fetch: typeof fetch }).fetch = vi.fn();
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      writable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
    Object.defineProperty(navigator, "share", {
      configurable: true,
      writable: true,
      value: undefined,
    });
  });

  it("рендерит крупный login screen с placeholder и телефоном", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response("unauthorized", { status: 401 }));

    render(<App />);

    await waitFor(() => expect(screen.getByText("Вход в систему")).toBeInTheDocument());
    expect(screen.getByPlaceholderText("Введите сюда свой логин")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Введите сюда свой пароль")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "+7 (910) 109-39-71" })).toHaveAttribute("href", "tel:+79101093971");
  });

  it("показывает профиль и карточки разделов на HomeScreen", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(mockSessionResponse()).mockResolvedValueOnce(mockResultListResponse());

    render(<App />);

    await waitFor(() => expect(screen.getByText("Иванов Иван Иванович")).toBeInTheDocument());
    expect(screen.getByText("Результаты анализов")).toBeInTheDocument();
    expect(screen.getByText("Запись на прием")).toBeInTheDocument();
    expect(screen.getByText("Бонусы и акции")).toBeInTheDocument();
    expect(screen.getByText("Перечень услуг")).toBeInTheDocument();
  });

  it("поддерживает bottom navigation и foundation screens", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(mockSessionResponse()).mockResolvedValueOnce(mockResultListResponse());

    render(<App />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Запись" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Запись" }));
    expect(screen.getByText("Foundation screen: данные врачей и слотов сейчас демо-конфиг.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Акции" }));
    expect(screen.getByText("Foundation screen: бонусная программа сейчас использует mock/config данные.")).toBeInTheDocument();
  });

  it("открывает details с форматированием и back navigation", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(mockSessionResponse())
      .mockResolvedValueOnce(mockResultListResponse())
      .mockResolvedValueOnce(mockResultDetailsResponse());

    render(<App />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Анализы" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Анализы" }));
    fireEvent.click(screen.getByText("Результат №125487"));

    await waitFor(() => expect(screen.getByText("Калий (К+): 4.2 ммоль/л")).toBeInTheDocument());
    expect(screen.getByText("Пролактин: 53.8 ++ нг/мл")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Назад" }));
    await waitFor(() => expect(screen.getByText("Результат №125487")).toBeInTheDocument());
  });

  it("рендерит pdf screen с back/top и action bar", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(mockSessionResponse())
      .mockResolvedValueOnce(mockResultListResponse())
      .mockResolvedValueOnce(mockResultDetailsResponse());

    render(<App />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Анализы" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Анализы" }));
    fireEvent.click(screen.getByText("Результат №125487"));
    await waitFor(() => expect(screen.getByRole("button", { name: "Открыть в PDF" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Открыть в PDF" }));

    expect(screen.getByTitle("PDF документ")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Отправить в MAX" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Поделиться" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Сохранить" })).toBeInTheDocument();
  });

  it("services screen поддерживает live search", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(mockSessionResponse()).mockResolvedValueOnce(mockResultListResponse());

    render(<App />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Услуги" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Услуги" }));
    fireEvent.change(screen.getByPlaceholderText("Поиск по услугам"), { target: { value: "Пролактин" } });

    fireEvent.click(screen.getByText("Биохимические исследования"));
    expect(screen.getByText("Пролактин")).toBeInTheDocument();
    expect(screen.queryByText("Консультация кардиолога")).not.toBeInTheDocument();
  });
});
