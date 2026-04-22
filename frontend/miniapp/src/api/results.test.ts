import { ApiClient } from "./client";
import { ResultsApi } from "./results";

describe("ResultsApi", () => {
  beforeEach(() => {
    (globalThis as { fetch: typeof fetch }).fetch = vi.fn();
  });

  it("обрабатывает успешный ответ", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify([{ result_id: "1", has_pdf: true }]), { status: 200 }));
    const api = new ResultsApi(new ApiClient({ baseUrl: "http://localhost" }));
    const payload = await api.list();
    expect(payload).toHaveLength(1);
  });

  it("обрабатывает получение details", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ result_id: "1", title: "ОАК", services: [], sections: [], indicators: [], has_pdf: false }), { status: 200 }));
    const api = new ResultsApi(new ApiClient({ baseUrl: "http://localhost" }));
    const payload = await api.get("1");
    expect(payload.result_id).toBe("1");
  });
});
