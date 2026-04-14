import type { PropsWithChildren } from "react";

export function MaxUI({ children }: PropsWithChildren): JSX.Element {
  return <div data-testid="max-ui-shell">{children}</div>;
}

export function Button(props: PropsWithChildren<{ onClick?: () => void; disabled?: boolean }>): JSX.Element {
  return (
    <button type="button" onClick={props.onClick} disabled={props.disabled}>
      {props.children}
    </button>
  );
}

export function Card({ children }: PropsWithChildren): JSX.Element {
  return <section>{children}</section>;
}
