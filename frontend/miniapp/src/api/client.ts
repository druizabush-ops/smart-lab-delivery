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
    const response = await fetch(`${this.options.baseUrl}${path}`);
    if (!response.ok) {
      throw new ApiError("Backend error", response.status);
    }
    return (await response.json()) as T;
  }
}
