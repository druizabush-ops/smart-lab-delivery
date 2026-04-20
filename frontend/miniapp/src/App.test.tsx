import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

describe("App auth flow", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    (globalThis as { fetch: typeof fetch }).fetch = vi.fn();
    window.WebApp = {
      initDataUnsafe: { user: { id: "patient-001" } },
      platform: "max-mobile",
      version: "1.0",
    };
  });

  it("показывает экран входа при отсутствии сессии", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response("unauthorized", { status: 401 }));
    render(<App />);
    await waitFor(() => expect(screen.getByText("Вход пациента")).toBeInTheDocument());
  });

  it("логин по логину и паролю и загрузка результатов", async () => {
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
      .mockResolvedValueOnce(new Response(JSON.stringify([{ result_id: "card-1", status: "max_sent", channel: "max", attempts_count: 1, documents: [], patient_id: "p1", created_at: "2026-01-01", updated_at: "2026-01-01", last_error: null }]), { status: 200 }));

    render(<App />);
    await waitFor(() => expect(screen.getByText("Вход пациента")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Вход по логину"));
    fireEvent.change(screen.getByPlaceholderText("Логин"), { target: { value: "demo" } });
    fireEvent.change(screen.getByPlaceholderText("Пароль"), { target: { value: "secret" } });
    fireEvent.click(screen.getByText("Войти"));

    await waitFor(() => expect(screen.getByText("Доступные результаты")).toBeInTheDocument());
  });
});
