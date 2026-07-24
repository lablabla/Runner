import {
  useClearInsights,
  useDeleteInsight,
  useGenerateWeeklySummary,
  useInsights,
} from "../api/hooks";
import { Badge, Button, Card, ErrorNote, Spinner } from "../components/ui";
import { dateTime } from "../format";

export default function InsightsPage() {
  const { data, isLoading } = useInsights();
  const generate = useGenerateWeeklySummary();
  const clearAll = useClearInsights();
  const deleteOne = useDeleteInsight();

  if (isLoading) return <Spinner />;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">Insights</h1>
        <div className="flex items-center gap-2">
          {!!data?.length && (
            <Button
              variant="ghost"
              onClick={() => {
                if (confirm("Clear all insights?")) clearAll.mutate();
              }}
              disabled={clearAll.isPending}
            >
              {clearAll.isPending ? "Clearing…" : "Clear all"}
            </Button>
          )}
          <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
            {generate.isPending ? "Generating…" : "Generate weekly summary"}
          </Button>
        </div>
      </div>

      {generate.isError && <ErrorNote message={(generate.error as Error).message} />}

      {!data?.length ? (
        <Card>
          <p className="text-sm text-ink-secondary">
            No insights yet. Configure an LLM provider on the Settings page, then generate a weekly summary or
            analyse an individual run from its detail page.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {data.map((i) => (
            <Card key={i.id}>
              <div className="mb-2 flex items-center gap-2 text-xs text-muted">
                <Badge>{i.kind.replace("_", " ")}</Badge>
                {i.period && <span>{i.period}</span>}
                <span className="ml-auto">{dateTime(i.created_at)}</span>
                {i.model && <span className="text-muted">· {i.model}</span>}
                <button
                  onClick={() => deleteOne.mutate(i.id)}
                  className="text-muted hover:text-ink"
                  aria-label="Delete insight"
                  title="Delete"
                >
                  ✕
                </button>
              </div>
              <p className="whitespace-pre-wrap text-sm text-ink-secondary">{i.content}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
