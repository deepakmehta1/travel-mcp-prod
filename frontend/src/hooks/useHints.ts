import { useEffect, useState } from "react";
import { AgentClient } from "../api/client";

export function useHints(
  client: AgentClient,
  trigger: any,
): [string[], boolean] {
  const [hints, setHints] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const fetchHints = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${client.baseUrl}/hints`);
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        if (!cancelled && Array.isArray(data.hints)) setHints(data.hints);
      } catch (_) {
        if (!cancelled) {
          setHints([
            "Find tours to Goa under 40000",
            "Show details for tour GOA-5D4N-OPT2",
            "Book GOA-5D4N-OPT2 starting next month",
          ]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchHints();
    return () => {
      cancelled = true;
    };
  }, [client, trigger]);

  return [hints, loading];
}
