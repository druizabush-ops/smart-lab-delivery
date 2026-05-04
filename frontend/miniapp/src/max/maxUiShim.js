import { jsx as _jsx } from "react/jsx-runtime";
export function MaxUI({ children }) {
    return _jsx("div", { "data-testid": "max-ui-shell", children: children });
}
export function Button(props) {
    return (_jsx("button", { type: "button", onClick: props.onClick, disabled: props.disabled, children: props.children }));
}
