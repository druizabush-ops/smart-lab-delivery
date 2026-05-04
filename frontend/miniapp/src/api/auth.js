export class AuthApi {
    constructor(client) {
        this.client = client;
    }
    login(login, password) {
        return this.client.post("/patient/auth/login", { login, password });
    }
    loginByPhone(phone) {
        return this.client.post("/patient/auth/phone", { phone });
    }
    confirmCode(patientId, code) {
        return this.client.post("/patient/auth/confirm-code", { patient_id: patientId, code });
    }
    me() {
        return this.client.get("/patient/auth/me");
    }
    logout() {
        return this.client.post("/patient/auth/logout");
    }
}
