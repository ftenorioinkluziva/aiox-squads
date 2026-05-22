import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "../services/api";
import type { PipelineEvent, PipelineRun } from "../types";

const ACTIVE_STATUSES = new Set(["queued", "running"]);

export function usePipeline(sessionId?: string, onCompleted?: () => void) {
  const [pipeline, setPipeline] = useState<PipelineRun | null>(null);
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const closeSocket = useCallback(() => {
    socketRef.current?.close();
    socketRef.current = null;
  }, []);

  const refresh = useCallback(async (runId: string) => {
    const data = await api.getPipeline(runId);
    setPipeline(data);
    setEvents(data.events || []);
    return data as PipelineRun;
  }, []);

  const connect = useCallback(
    (runId: string) => {
      closeSocket();
      const socket = new WebSocket(api.pipelineWebSocketUrl(runId));
      socketRef.current = socket;
      socket.onmessage = async (message) => {
        const event = JSON.parse(message.data) as PipelineEvent;
        if (event.event_type === "snapshot") {
          setPipeline(event.payload as unknown as PipelineRun);
          setEvents((event.payload as any).events || []);
          return;
        }
        setEvents((prev) => [...prev, event]);
        const updated = await refresh(runId);
        if (updated.status === "completed") onCompleted?.();
        if (!ACTIVE_STATUSES.has(updated.status)) closeSocket();
      };
      socket.onerror = () => setError("Conexao em tempo real indisponivel");
    },
    [closeSocket, onCompleted, refresh],
  );

  useEffect(() => {
    closeSocket();
    setPipeline(null);
    setEvents([]);
    setError(null);
    if (!sessionId) return;

    let cancelled = false;
    api.getLatestPipeline(sessionId)
      .then(({ pipeline }) => {
        if (cancelled) return;
        setPipeline(pipeline);
        setEvents(pipeline?.events || []);
        if (pipeline && ACTIVE_STATUSES.has(pipeline.status)) {
          connect(pipeline.id);
        }
      })
      .catch((e: any) => setError(e.message));

    return () => {
      cancelled = true;
      closeSocket();
    };
  }, [closeSocket, connect, sessionId]);

  const start = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.startPipeline({ session_id: sessionId });
      setPipeline(data);
      setEvents(data.events || []);
      if (ACTIVE_STATUSES.has(data.status)) connect(data.id);
    } catch (e: any) {
      setError(e.message || "Erro ao iniciar pipeline");
    } finally {
      setLoading(false);
    }
  }, [connect, sessionId]);

  return {
    pipeline,
    events,
    loading,
    error,
    start,
    clearError: () => setError(null),
  };
}
