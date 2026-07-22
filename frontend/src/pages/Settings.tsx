import { useState } from "react";

import { api } from "../api/client";
import {
  useConfigureLLM,
  useConnectGarmin,
  useDisconnect,
  useIntegrations,
  useMe,
} from "../api/hooks";
import { Badge, Button, Card, ErrorNote, Spinner } from "../components/ui";
import { dateTime } from "../format";

const LLM_PROVIDERS = [
  { value: "none", label: "Disabled" },
  { value: "anthropic", label: "Anthropic Claude" },
  { value: "openai", label: "OpenAI" },
  { value: "gemini", label: "Google Gemini" },
  { value: "ollama", label: "Ollama (local)" },
];

function statusColor(status: string): string {
  if (status === "connected") return "var(--status-good)";
  if (status === "error") return "var(--status-critical)";
  return "var(--muted)";
}

export default function SettingsPage() {
  const me = useMe();
  const integrations = useIntegrations();
  const connectGarmin = useConnectGarmin();
  const configureLLM = useConfigureLLM();
  const disconnect = useDisconnect();

  const [gUser, setGUser] = useState("");
  const [gPass, setGPass] = useState("");
  const [provider, setProvider] = useState("anthropic");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("claude-opus-4-8");
  const [stravaBusy, setStravaBusy] = useState(false);

  if (integrations.isLoading || me.isLoading) return <Spinner />;

  const byProvider = (p: string) => integrations.data?.find((i) => i.provider === p);

  const startStrava = async () => {
    setStravaBusy(true);
    try {
      const { authorize_url } = await api<{ authorize_url: string }>("/integrations/strava/authorize");
      window.location.href = authorize_url;
    } catch (err) {
      alert((err as Error).message);
      setStravaBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Settings</h1>

      {/* Garmin */}
      <Card>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Garmin Connect</h3>
          <StatusBadge status={byProvider("garmin")?.status} />
        </div>
        <p className="mb-3 text-sm text-ink-secondary">
          Your Garmin credentials are encrypted at rest and used only to fetch your activities and health
          metrics. They are never stored in plaintext or shared.
        </p>
        {byProvider("garmin") ? (
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted">
              Last sync: {byProvider("garmin")?.last_sync_at ? dateTime(byProvider("garmin")!.last_sync_at!) : "never"}
            </span>
            <Button variant="ghost" onClick={() => disconnect.mutate("garmin")}>
              Disconnect
            </Button>
          </div>
        ) : (
          <form
            className="grid gap-3 sm:grid-cols-3"
            onSubmit={(e) => {
              e.preventDefault();
              connectGarmin.mutate({ username: gUser, password: gPass });
            }}
          >
            <input
              placeholder="Garmin email"
              value={gUser}
              onChange={(e) => setGUser(e.target.value)}
              className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm"
              required
            />
            <input
              type="password"
              placeholder="Garmin password"
              value={gPass}
              onChange={(e) => setGPass(e.target.value)}
              className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm"
              required
            />
            <Button type="submit" disabled={connectGarmin.isPending}>
              {connectGarmin.isPending ? "Connecting…" : "Connect"}
            </Button>
          </form>
        )}
        {connectGarmin.isError && <div className="mt-3"><ErrorNote message={(connectGarmin.error as Error).message} /></div>}
      </Card>

      {/* Strava */}
      <Card>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Strava</h3>
          <StatusBadge status={byProvider("strava")?.status} />
        </div>
        <p className="mb-3 text-sm text-ink-secondary">
          Optional secondary source, connected via Strava's official OAuth. Requires STRAVA_CLIENT_ID /
          SECRET set on the server.
        </p>
        {byProvider("strava") ? (
          <Button variant="ghost" onClick={() => disconnect.mutate("strava")}>
            Disconnect
          </Button>
        ) : (
          <Button onClick={startStrava} disabled={stravaBusy}>
            {stravaBusy ? "Redirecting…" : "Connect Strava"}
          </Button>
        )}
      </Card>

      {/* LLM */}
      <Card>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">AI analysis (LLM)</h3>
          <StatusBadge status={byProvider("llm")?.status} />
        </div>
        <p className="mb-3 text-sm text-ink-secondary">
          Choose a provider for coach-style summaries. Keys are stored encrypted. Ollama runs a local model on
          the Pi and needs no key.
        </p>
        <form
          className="grid gap-3 sm:grid-cols-4"
          onSubmit={(e) => {
            e.preventDefault();
            configureLLM.mutate({ provider, api_key: apiKey || undefined, model: model || undefined });
          }}
        >
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm"
          >
            {LLM_PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
          <input
            placeholder="Model (optional)"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm"
          />
          <input
            type="password"
            placeholder="API key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            disabled={provider === "ollama" || provider === "none"}
            className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm disabled:opacity-50"
          />
          <Button type="submit" disabled={configureLLM.isPending}>
            Save
          </Button>
        </form>
      </Card>

      {/* Profile / home location */}
      <HomeLocationCard
        lat={me.data?.home_lat ?? null}
        lon={me.data?.home_lon ?? null}
        onSaved={() => me.refetch()}
      />
    </div>
  );
}

function StatusBadge({ status }: { status?: string }) {
  if (!status) return <Badge>not connected</Badge>;
  return <Badge color={statusColor(status)}>{status}</Badge>;
}

function HomeLocationCard({
  lat,
  lon,
  onSaved,
}: {
  lat: number | null;
  lon: number | null;
  onSaved: () => void;
}) {
  const [la, setLa] = useState(lat?.toString() ?? "");
  const [lo, setLo] = useState(lon?.toString() ?? "");
  const [busy, setBusy] = useState(false);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api("/auth/me", {
        method: "PATCH",
        body: JSON.stringify({ home_lat: la ? Number(la) : null, home_lon: lo ? Number(lo) : null }),
      });
      onSaved();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <h3 className="mb-1 text-sm font-semibold">Home location</h3>
      <p className="mb-3 text-sm text-ink-secondary">
        Used as a weather fallback for runs recorded without GPS (e.g. treadmill).
      </p>
      <form className="grid gap-3 sm:grid-cols-3" onSubmit={save}>
        <input
          placeholder="Latitude"
          value={la}
          onChange={(e) => setLa(e.target.value)}
          className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm"
        />
        <input
          placeholder="Longitude"
          value={lo}
          onChange={(e) => setLo(e.target.value)}
          className="rounded-lg border border-hairline bg-plane px-3 py-2 text-sm"
        />
        <Button type="submit" disabled={busy}>
          Save
        </Button>
      </form>
    </Card>
  );
}
