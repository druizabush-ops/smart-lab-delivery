export class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}
export class ApiClient {
    constructor(options) {
        this.options = options;
    }
    async get(path) {
        const response = await fetch(`${this.options.baseUrl}${path}`, { credentials: "include" });
        if (!response.ok) {
            throw new ApiError("Backend error", response.status);
        }
        return (await response.json());
    }
    async post(path, body) {
        const response = await fetch(`${this.options.baseUrl}${path}`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: body ? JSON.stringify(body) : undefined,
        });
        if (!response.ok) {
            throw new ApiError("Backend error", response.status);
        }
        return (await response.json());
    }
}
