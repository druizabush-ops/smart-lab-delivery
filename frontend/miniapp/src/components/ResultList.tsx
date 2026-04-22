import { Button } from "@maxhub/max-ui";
import type { PatientResultListItem } from "../api/results";
import { miniAppContentConfig } from "../ui/contentConfig";

export function ResultList(props: {
  results: PatientResultListItem[];
  onOpen: (id: string) => void;
  onOpenPdf: (id: string) => void;
  onDownloadPdf: (id: string) => void;
}): JSX.Element {
  return (
    <div className="results-list">
      <h2>{miniAppContentConfig.results.title}</h2>
      {props.results.map((result) => (
        <section key={result.result_id} className="result-card">
          <p className="result-card__title">Результат №{result.result_id}</p>
          <p className="result-card__meta">{result.date ?? "—"}</p>
          {result.lab_name ? <p className="result-card__meta">{result.lab_name}</p> : null}
          <p className="result-status">Статус: {result.status}</p>
          <div className="result-card__actions">
            <Button onClick={() => props.onOpen(result.result_id)}>{miniAppContentConfig.results.openButton}</Button>
            <Button disabled={!result.has_pdf} onClick={() => props.onOpenPdf(result.result_id)}>
              {miniAppContentConfig.results.openPdfButton}
            </Button>
            <Button disabled={!result.has_pdf} onClick={() => props.onDownloadPdf(result.result_id)}>
              {miniAppContentConfig.results.downloadPdfButton}
            </Button>
          </div>
        </section>
      ))}
    </div>
  );
}
