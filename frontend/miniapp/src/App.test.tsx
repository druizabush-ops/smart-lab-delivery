import { render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

describe("App", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    (global as { fetch: typeof fetch }).fetch = vi.fn();
    window.WebApp = {
      initDataUnsafe: { user: { id: "patient-001" } },
      platform: "max-mobile",
      version: "1.0",
    };
  });

  it("рендерит список результатов", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify([{ result_id: "card-1", status: "max_sent", channel: "max", attempts_count: 1, documents: [], patient_id: "patient-001", created_at: "2026-01-01", updated_at: "2026-01-01", last_error: null }]), { status: 200 }),
    );

    render(<App />);
    await waitFor(() => expect(screen.getByText("Доступные результаты")).toBeInTheDocument());
    expect(screen.getByText(/card-1/)).toBeInTheDocument();
  });

  it("рендерит no-results state", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));
    render(<App />);
    await waitFor(() => expect(screen.getByText(/нет доступных результатов/)).toBeInTheDocument());
  });

  it("рендерит error state", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response("boom", { status: 500 }));
    render(<App />);
    await waitFor(() => expect(screen.getByText(/Ошибка API/)).toBeInTheDocument());
  });

  it("читает start_param", async () => {
    window.WebApp = {
      initDataUnsafe: { user: { id: "patient-001" }, start_param: "result:card-77" },
      platform: "max-mobile",
      version: "1.0",
    };
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify([{ result_id: "card-77", status: "max_sent", channel: "max", attempts_count: 1, documents: [], patient_id: "patient-001", created_at: "2026-01-01", updated_at: "2026-01-01", last_error: null }]), { status: 200 }),
    );
    render(<App />);
    await waitFor(() => expect(screen.getByText(/start_param: result:card-77/)).toBeInTheDocument());
    expect(screen.getByText(/Детали результата/)).toBeInTheDocument();
  });

  it("fallback вне MAX", async () => {
    // @ts-expect-error intentional empty context
    window.WebApp = undefined;
    render(<App />);
    expect(screen.getByText(/Режим вне MAX/)).toBeInTheDocument();
    expect(screen.getByText(/Не удалось определить patient_id/)).toBeInTheDocument();
  });
});
