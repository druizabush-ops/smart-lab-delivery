import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Button } from "@maxhub/max-ui";
export function ResultList(props) {
    return (_jsxs("div", { children: [_jsx("h2", { children: "\u0414\u043E\u0441\u0442\u0443\u043F\u043D\u044B\u0435 \u0440\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442\u044B" }), props.results.map((result) => (_jsxs("section", { children: [_jsxs("p", { children: ["ID: ", result.result_id] }), _jsxs("p", { children: ["\u0421\u0442\u0430\u0442\u0443\u0441: ", result.status] }), _jsxs("p", { children: ["\u041A\u0430\u043D\u0430\u043B: ", result.channel] }), _jsx(Button, { onClick: () => props.onOpen(result.result_id), children: "\u041E\u0442\u043A\u0440\u044B\u0442\u044C" })] }, result.result_id)))] }));
}
