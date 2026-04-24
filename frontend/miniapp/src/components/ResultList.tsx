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
        <section
          key={result.result_id}
          className="result-card result-card--clickable"
          role="button"
          tabIndex={0}
          onClick={() => props.onOpen(result.result_id)}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              props.onOpen(result.result_id);
            }
          }}
        >
          <p className="result-card__title">Результат №{result.result_id}</p>
          <p className="result-card__meta">{result.date ?? "—"}</p>
          <p className="result-status">{result.status || miniAppContentConfig.results.readyLabel}</p>
          <div className="result-card__actions">
            <button type="button" className="icon-action-button" onClick={(event) => { event.stopPropagation(); props.onOpen(result.result_id); }}>
              {miniAppContentConfig.results.openLabel}
            </button>
            <button type="button" className="icon-action-button" disabled={!result.has_pdf} onClick={(event) => { event.stopPropagation(); props.onOpenPdf(result.result_id); }}>
              PDF
            </button>
            <button type="button" className="icon-action-button" disabled={!result.has_pdf} onClick={(event) => { event.stopPropagation(); props.onDownloadPdf(result.result_id); }}>
              ↓
            </button>
          </div>
        </section>
      ))}
    </div>
  );
}
