import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { Button, Card, ErrorNote } from "../components/ui";
import { Field } from "./Login";

export default function RegisterPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, display_name: name || null }),
      });
      await signIn(email, password);
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <h1 className="mb-1 text-xl font-semibold">Create account</h1>
        <p className="mb-4 text-sm text-ink-secondary">The first account becomes the admin.</p>
        <form onSubmit={submit} className="space-y-3">
          <Field label="Display name (optional)" value={name} onChange={setName} />
          <Field label="Email" type="email" value={email} onChange={setEmail} />
          <Field label="Password (min 8 chars)" type="password" value={password} onChange={setPassword} />
          {error && <ErrorNote message={error} />}
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? "Creating…" : "Create account"}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-ink-secondary">
          Have an account?{" "}
          <Link to="/login" className="text-brand hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}
