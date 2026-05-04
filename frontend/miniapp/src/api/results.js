export class ResultsApi {
    constructor(client) {
        this.client = client;
    }
    list() {
        return this.client.get("/patient/results");
    }
    get(resultId) {
        return this.client.get(`/patient/results/${encodeURIComponent(resultId)}`);
    }
}
