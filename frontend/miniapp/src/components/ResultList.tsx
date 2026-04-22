import { Button } from "@maxhub/max-ui";
import type { PatientResultListItem } from "../api/results";

export function ResultList(props: {
  results: PatientResultListItem[];
  onOpen: (id: string) => void;
  onOpenPdf: (id: string) => void;
  onDownloadPdf: (id: string) => void;
}): JSX.Element {
  return (
    <div>
      <h2>Результаты анализов</h2>
      {props.results.map((result) => (
        <section key={result.result_id}>
          <p>{result.title}</p>
          <p>Дата: {result.date ?? "—"}</p>
          <p>Статус: {result.status}</p>
          <Button onClick={() => props.onOpen(result.result_id)}>Открыть</Button>
          <Button disabled={!result.has_pdf} onClick={() => props.onOpenPdf(result.result_id)}>
            Открыть PDF
          </Button>
          <Button disabled={!result.has_pdf} onClick={() => props.onDownloadPdf(result.result_id)}>
            Скачать PDF
          </Button>
        </section>
      ))}
    </div>
  );
}
