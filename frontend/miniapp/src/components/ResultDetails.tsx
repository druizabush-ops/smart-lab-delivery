import { Button } from "@maxhub/max-ui";
import type { PatientResult } from "../api/results";

export function ResultDetails(props: { result: PatientResult; onBack: () => void }): JSX.Element {
  return (
    <div>
      <Button onClick={props.onBack}>Назад к списку</Button>
      <h2>Детали результата</h2>
      <p>Статус: {props.result.status}</p>
      <p>Попыток отправки: {props.result.attempts_count}</p>
      {props.result.last_error ? <p>Последняя ошибка: {props.result.last_error}</p> : null}
      <h3>Документы</h3>
      {props.result.documents.map((doc) => (
        <div key={doc.title}>
          <span>{doc.title} — {doc.readiness}</span>
          {doc.url ? (
            <a href={doc.url} target="_blank" rel="noreferrer">
              Открыть
            </a>
          ) : (
            <span> Файл пока недоступен</span>
          )}
        </div>
      ))}
    </div>
  );
}
