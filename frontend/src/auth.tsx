import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { getToken, login as apiLogin, setToken } from "./api/client";

interface AuthCtx {
  authed: boolean;
  ready: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

const Ctx = createContext<AuthCtx>({
  authed: false,
  ready: false,
  signIn: async () => {},
  signOut: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authed, setAuthed] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setAuthed(!!getToken());
    setReady(true);
  }, []);

  const signIn = async (email: string, password: string) => {
    const token = await apiLogin(email, password);
    setToken(token);
    setAuthed(true);
  };

  const signOut = () => {
    setToken(null);
    setAuthed(false);
  };

  return <Ctx.Provider value={{ authed, ready, signIn, signOut }}>{children}</Ctx.Provider>;
}

export const useAuth = () => useContext(Ctx);
