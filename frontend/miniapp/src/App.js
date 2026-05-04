import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { MaxUI } from "@maxhub/max-ui";
import { ApiClient, ApiError } from "./api/client";
import { ResultsApi } from "./api/results";
import { AuthApi } from "./api/auth";
import { ResultDetails } from "./components/ResultDetails";
import { ResultList } from "./components/ResultList";
import { getMaxContext, parseStartParam } from "./max/context";
export function resolvePatientApiBaseUrl() {
    const configuredBaseUrl = import.meta.env.VITE_PATIENT_API_BASE_URL;
    if (configuredBaseUrl && configuredBaseUrl.trim().length > 0) {
        return configuredBaseUrl;
    }
    return "/api/patient";
}
export function App() {
    const context = getMaxContext();
    const start = parseStartParam(context.startParam);
    const baseUrl = resolvePatientApiBaseUrl();
    const client = useMemo(() => new ApiClient({ baseUrl }), [baseUrl]);
    const resultsApi = useMemo(() => new ResultsApi(client), [client]);
    const authApi = useMemo(() => new AuthApi(client), [client]);
    const [results, setResults] = useState([]);
    const [session, setSession] = useState(null);
    const [selectedId, setSelectedId] = useState(start.mode === "result" ? start.resultId ?? null : null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [authMode, setAuthMode] = useState("chooser");
    const [pendingPatientId, setPendingPatientId] = useState("");
    const [login, setLogin] = useState("");
    const [password, setPassword] = useState("");
    const [phone, setPhone] = useState("");
    const [code, setCode] = useState("");
    useEffect(() => {
        authApi
            .me()
            .then((currentSession) => {
            setSession(currentSession);
            return resultsApi.list();
        })
            .then((items) => setResults(items))
            .catch(() => {
            setSession(null);
        })
            .finally(() => setLoading(false));
    }, [authApi, resultsApi]);
    const selected = selectedId ? results.find((result) => result.result_id === selectedId) ?? null : null;
    const handleLoginSubmit = async () => {
        try {
            setError(null);
            const currentSession = await authApi.login(login, password);
            setSession(currentSession);
            const items = await resultsApi.list();
            setResults(items);
        }
        catch (err) {
            setError(err instanceof ApiError ? "Неверный логин/пароль" : "Ошибка входа");
        }
    };
    const handlePhoneSubmit = async () => {
        try {
            setError(null);
            const pending = await authApi.loginByPhone(phone);
            setPendingPatientId(pending.patient_id);
            setAuthMode("code");
        }
        catch {
            setError("Ошибка входа по телефону");
        }
    };
    const handleCodeSubmit = async () => {
        try {
            setError(null);
            const currentSession = await authApi.confirmCode(pendingPatientId, code);
            setSession(currentSession);
            const items = await resultsApi.list();
            setResults(items);
        }
        catch {
            setError("Неверный SMS-код");
        }
    };
    const handleLogout = async () => {
        await authApi.logout();
        setSession(null);
        setResults([]);
        setSelectedId(null);
        setAuthMode("chooser");
    };
    return (_jsx(MaxUI, { children: _jsxs("main", { children: [_jsx("h1", { children: "Smart Lab Results" }), !context.isInsideMax ? _jsx("p", { children: "\u0420\u0435\u0436\u0438\u043C \u0432\u043D\u0435 MAX: \u0438\u0441\u043F\u043E\u043B\u044C\u0437\u0443\u0435\u0442\u0441\u044F fallback-\u043A\u043E\u043D\u0442\u0435\u043A\u0441\u0442." }) : null, loading ? _jsx("p", { children: "\u0417\u0430\u0433\u0440\u0443\u0437\u043A\u0430..." }) : null, !loading && !session ? (_jsxs("section", { children: [_jsx("h2", { children: "\u0412\u0445\u043E\u0434 \u043F\u0430\u0446\u0438\u0435\u043D\u0442\u0430" }), authMode === "chooser" ? (_jsxs(_Fragment, { children: [_jsx("button", { onClick: () => setAuthMode("login"), children: "\u0412\u0445\u043E\u0434 \u043F\u043E \u043B\u043E\u0433\u0438\u043D\u0443" }), _jsx("button", { onClick: () => setAuthMode("phone"), children: "\u0412\u0445\u043E\u0434 \u043F\u043E \u0442\u0435\u043B\u0435\u0444\u043E\u043D\u0443" })] })) : null, authMode === "login" ? (_jsxs(_Fragment, { children: [_jsx("input", { placeholder: "\u041B\u043E\u0433\u0438\u043D", value: login, onChange: (e) => setLogin(e.target.value) }), _jsx("input", { placeholder: "\u041F\u0430\u0440\u043E\u043B\u044C", type: "password", value: password, onChange: (e) => setPassword(e.target.value) }), _jsx("button", { onClick: handleLoginSubmit, children: "\u0412\u043E\u0439\u0442\u0438" })] })) : null, authMode === "phone" ? (_jsxs(_Fragment, { children: [_jsx("input", { placeholder: "\u0422\u0435\u043B\u0435\u0444\u043E\u043D", value: phone, onChange: (e) => setPhone(e.target.value) }), _jsx("button", { onClick: handlePhoneSubmit, children: "\u041F\u043E\u043B\u0443\u0447\u0438\u0442\u044C \u043A\u043E\u0434" })] })) : null, authMode === "code" ? (_jsxs(_Fragment, { children: [_jsx("input", { placeholder: "SMS-\u043A\u043E\u0434", value: code, onChange: (e) => setCode(e.target.value) }), _jsx("button", { onClick: handleCodeSubmit, children: "\u041F\u043E\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044C \u043A\u043E\u0434" })] })) : null] })) : null, !loading && session ? (_jsxs("section", { children: [_jsxs("p", { children: ["\u041F\u0430\u0446\u0438\u0435\u043D\u0442: ", session.patient_name || session.patient_number] }), _jsx("button", { onClick: handleLogout, children: "\u0412\u044B\u0439\u0442\u0438" }), error ? _jsx("p", { children: error }) : null, !error && results.length === 0 ? _jsx("p", { children: "\u0423 \u043F\u0430\u0446\u0438\u0435\u043D\u0442\u0430 \u043F\u043E\u043A\u0430 \u043D\u0435\u0442 \u0434\u043E\u0441\u0442\u0443\u043F\u043D\u044B\u0445 \u0440\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442\u043E\u0432." }) : null, !error && results.length > 0 && !selected ? _jsx(ResultList, { results: results, onOpen: setSelectedId }) : null, !error && selected ? _jsx(ResultDetails, { result: selected, onBack: () => setSelectedId(null) }) : null] })) : null, error ? _jsx("p", { children: error }) : null] }) }));
}
