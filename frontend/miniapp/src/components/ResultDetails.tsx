import { Button } from "@maxhub/max-ui";
import type { PatientResultDetails } from "../api/results";

export function ResultDetails(props: {
  result: PatientResultDetails;
  onBack: () => void;
  onOpenPdf: () => void;
  onDownloadPdf: () => void;
}): JSX.Element {
  return (
    <div className="result-details">
      <Button onClick={props.onBack}>Назад к списку</Button>
      <h2>{props.result.title}</h2>
      <p>Дата: {props.result.date ?? "—"}</p>
      <p>Статус: {props.result.status}</p>
      <p>Лаборатория: {props.result.lab_name ?? "—"}</p>
      <h3>Показатели</h3>
      {props.result.indicators.length === 0 ? <p>Показатели пока недоступны.</p> : null}
      {props.result.indicators.map((item, index) => (
        <p key={index}>{String(item.name ?? "Показатель")}: {String(item.value ?? "—")}</p>
      ))}
      <div className="result-card__actions">
        <Button disabled={!props.result.has_pdf} onClick={props.onOpenPdf}>Открыть PDF</Button>
        <Button disabled={!props.result.has_pdf} onClick={props.onDownloadPdf}>Скачать PDF</Button>
      </div>
    </div>
  );
}
