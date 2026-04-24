import type { PatientResultDetails } from "../api/results";
import { miniAppContentConfig } from "../ui/contentConfig";
import { buildPatientIndicators } from "../utils/patientResults";

export function ResultDetails(props: {
  result: PatientResultDetails;
  onBack: () => void;
  onOpenPdf: () => void;
  onDownloadPdf: () => void;
}): JSX.Element {
  return (
    <div className="result-details">
      <button type="button" onClick={props.onBack}>Назад</button>
      <h2>Исследование №{props.result.result_id}</h2>
      {buildPatientIndicators(props.result).map((item) => <p key={item.id}>{item.line}</p>)}
      <button type="button" disabled={!props.result.has_pdf} onClick={props.onOpenPdf}>{miniAppContentConfig.resultDetails.openPdfLabel}</button>
      <button type="button" disabled={!props.result.has_pdf} onClick={props.onDownloadPdf}>{miniAppContentConfig.pdfViewer.save}</button>
    </div>
  );
}
