import { Button } from "@maxhub/max-ui";
import type { PatientResultDetails } from "../api/results";
import { miniAppContentConfig } from "../ui/contentConfig";
import { buildPatientIndicators } from "../utils/patientResults";

export function ResultDetails(props: {
  result: PatientResultDetails;
  onBack: () => void;
  onOpenPdf: () => void;
  onDownloadPdf: () => void;
}): JSX.Element {
  const indicators = buildPatientIndicators(props.result);

  return (
    <div className="result-details">
      <Button onClick={props.onBack}>{miniAppContentConfig.details.backButton}</Button>
      <h2>{miniAppContentConfig.details.title}</h2>
      <p>Номер результата: {props.result.result_id}</p>
      <p>Дата: {props.result.date ?? "—"}</p>
      <p>Статус: {props.result.status}</p>
      <p>Лаборатория: {props.result.lab_name ?? "—"}</p>
      <h3>{miniAppContentConfig.details.indicatorsTitle}</h3>
      {indicators.length === 0 ? <p>{miniAppContentConfig.details.indicatorsEmpty}</p> : null}
      {indicators.map((item) => (
        <p key={item.id} className="indicator-line">{item.line}</p>
      ))}
      <div className="result-card__actions">
        <Button disabled={!props.result.has_pdf} onClick={props.onOpenPdf}>{miniAppContentConfig.details.openPdfButton}</Button>
        <Button disabled={!props.result.has_pdf} onClick={props.onDownloadPdf}>{miniAppContentConfig.details.downloadPdfButton}</Button>
      </div>
    </div>
  );
}
