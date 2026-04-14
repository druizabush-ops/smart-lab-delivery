import { Card, Button } from "@maxhub/max-ui";
import type { PatientResult } from "../api/results";

export function ResultList(props: { results: PatientResult[]; onOpen: (id: string) => void }): JSX.Element {
  return (
    <div>
      <h2>Доступные результаты</h2>
      {props.results.map((result) => (
        <Card key={result.result_id}>
          <p>ID: {result.result_id}</p>
          <p>Статус: {result.status}</p>
          <p>Канал: {result.channel}</p>
          <Button onClick={() => props.onOpen(result.result_id)}>Открыть</Button>
        </Card>
      ))}
    </div>
  );
}
