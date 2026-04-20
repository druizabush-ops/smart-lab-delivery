export class ApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
  }
}

export type ApiClientOptions = {
  baseUrl: string;
};

export class ApiClient {
  constructor(private readonly options: ApiClientOptions) {}

  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.options.baseUrl}${path}`, { credentials: "include" });
    if (!response.ok) {
      throw new ApiError("Backend error", response.status);
    }
    return (await response.json()) as T;
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const response = await fetch(`${this.options.baseUrl}${path}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      throw new ApiError("Backend error", response.status);
    }
    return (await response.json()) as T;
  }
}
