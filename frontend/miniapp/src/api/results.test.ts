import { ApiClient } from "./client";
import { ResultsApi } from "./results";

describe("ResultsApi", () => {
  beforeEach(() => {
    (global as { fetch: typeof fetch }).fetch = vi.fn();
  });

  it("обрабатывает успешный ответ", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify([{ result_id: "1" }]), { status: 200 }));
    const api = new ResultsApi(new ApiClient({ baseUrl: "http://localhost" }));
    const payload = await api.list("patient-1");
    expect(payload).toHaveLength(1);
  });

  it("обрабатывает ошибку backend", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response("error", { status: 500 }));
    const api = new ResultsApi(new ApiClient({ baseUrl: "http://localhost" }));
    await expect(api.list("patient-1")).rejects.toThrow(/Backend error/);
  });

  it("обрабатывает пустой результат", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));
    const api = new ResultsApi(new ApiClient({ baseUrl: "http://localhost" }));
    const payload = await api.list("patient-1");
    expect(payload).toEqual([]);
  });
});
