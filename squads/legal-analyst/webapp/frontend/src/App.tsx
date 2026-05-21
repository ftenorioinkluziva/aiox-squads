import { useCallback, useEffect, useRef, useState } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChatInterface from "./components/ChatInterface";
import PDFViewer from "./components/PDFViewer";
import AgentPanel from "./components/AgentPanel";
import LegalEditor from "./components/LegalEditor";
import VSLPage from "./pages/VSLPage";
import { useChat } from "./hooks/useChat";
import { useAgents } from "./hooks/useAgents";
import { usePDF } from "./hooks/usePDF";
import * as api from "./services/api";
import type { PanelView, SessionSummary } from "./types";

const LAST_SESSION_KEY = "legal-analyst:last-session-id";

export default function App() {
  const [activeView, setActiveView] = useState<PanelView>("chat");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [showVSL, setShowVSL] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("success") === "true") return false;
    if (window.location.pathname === "/app") return false;
    return true;
  });

  const chat = useChat();
  const agents = useAgents();
  const pdf = usePDF();
  const didBootstrap = useRef(false);

  useEffect(() => {
    if (showVSL) return;
    if (didBootstrap.current) return;
    didBootstrap.current = true;

    async function bootstrapSession() {
      const savedSessionId = window.localStorage.getItem(LAST_SESSION_KEY);

      if (savedSessionId) {
        const session = await chat.loadSession(savedSessionId);
        if (session?.session_id) {
          pdf.syncDocuments(session.documents || []);
          const updated = await api.listSessions().catch(() => []);
          setSessions(updated);
          return;
        }
        window.localStorage.removeItem(LAST_SESSION_KEY);
      }

      const session = await chat.initSession("Nova Analise Juridica");
      if (session?.session_id) {
        window.localStorage.setItem(LAST_SESSION_KEY, session.session_id);
        pdf.syncDocuments(session.documents || []);
      }
      const updated = await api.listSessions().catch(() => []);
      setSessions(updated);
    }

    bootstrapSession();
  }, [showVSL]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAccessApp = useCallback(() => {
    setShowVSL(false);
    window.history.pushState({}, "", "/app");
  }, []);

  const handleNewSession = useCallback(async () => {
    const session = await chat.initSession("Nova Analise");
    if (session?.session_id) {
      window.localStorage.setItem(LAST_SESSION_KEY, session.session_id);
    }
    pdf.syncDocuments(session?.documents || []);
    const updated = await api.listSessions().catch(() => []);
    setSessions(updated);
  }, [chat, pdf]);

  const handleLoadSession = useCallback(
    async (sessionId: string) => {
      const session = await chat.loadSession(sessionId);
      window.localStorage.setItem(LAST_SESSION_KEY, sessionId);
      pdf.syncDocuments(session?.documents || []);
    },
    [chat, pdf],
  );

  const handleUploadPDF = useCallback(
    async (file: File) => {
      if (!chat.session) return;
      try {
        const result = await pdf.upload(file, chat.session.session_id);
        // Send intake message
        await chat.sendMessage(
          `*intake PDF enviado: ${file.name} (${result.total_pages} paginas)`,
        );
      } catch (e: any) {
        chat.setError(e.message || "Erro no upload");
      }
    },
    [chat, pdf],
  );

  const handleClip = useCallback(
    async (data: {
      doc_id: string;
      page_start: number;
      page_end?: number;
      clip_type: string;
      label: string;
    }) => {
      await pdf.clipRegion(data);
    },
    [pdf],
  );

  const handleDraft = useCallback(
    async (data: {
      piece_type: string;
      considerations: string;
      instructions: string;
      clips: string[];
      references: any[];
    }) => {
      if (!chat.session) return;
      try {
        await api.draftPiece({
          session_id: chat.session.session_id,
          ...data,
        });
        await chat.loadSession(chat.session.session_id);
        setActiveView("chat");
      } catch (e: any) {
        chat.setError(e.message);
      }
    },
    [chat],
  );

  const handleReport = useCallback(
    async (focusAreas: string[]) => {
      if (!chat.session) return;
      try {
        await api.strategicReport({
          session_id: chat.session.session_id,
          focus_areas: focusAreas,
        });
        await chat.loadSession(chat.session.session_id);
        setActiveView("chat");
      } catch (e: any) {
        chat.setError(e.message);
      }
    },
    [chat],
  );

  const handleSelectAgent = useCallback(
    (agentId: string) => {
      setActiveView("chat");
      chat.sendMessage(`Acionando @${agentId}`, undefined, undefined, agentId);
    },
    [chat],
  );

  const handleReferenceClick = useCallback(
    (docId: string, page?: number) => {
      const doc = pdf.documents.find((d) => d.doc_id === docId);
      if (doc) {
        pdf.setActiveDoc(doc);
        if (page) pdf.setActivePage(page);
        setActiveView("documents");
      }
    },
    [pdf],
  );

  if (showVSL) {
    return <VSLPage onAccessApp={handleAccessApp} />;
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header
        sessionPhase={chat.session?.phase}
        sessionTitle={chat.session?.title}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeView={activeView}
          onViewChange={setActiveView}
          sessions={sessions}
          onNewSession={handleNewSession}
          onLoadSession={handleLoadSession}
          activeSessionId={chat.session?.session_id}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          documentCount={pdf.documents.length}
          agentCount={agents.agents.length}
        />

        <main className="flex-1 flex flex-col overflow-hidden bg-legal-navy">
          {activeView === "chat" && (
            <ChatInterface
              messages={chat.messages}
              isLoading={chat.isLoading}
              error={chat.error}
              scrollRef={chat.scrollRef}
              onSendMessage={chat.sendMessage}
              onUploadPDF={handleUploadPDF}
              onDismissError={() => chat.setError(null)}
              onReferenceClick={handleReferenceClick}
              documentCount={pdf.documents.length}
              documents={pdf.documents}
            />
          )}

          {activeView === "documents" && (
            <PDFViewer
              documents={pdf.documents}
              activeDoc={pdf.activeDoc}
              onSelectDoc={pdf.setActiveDoc}
              activePage={pdf.activePage}
              onPageChange={pdf.setActivePage}
              onLoadPage={pdf.loadPage}
              onClip={handleClip}
              onSearch={pdf.searchInDoc}
              searchResults={pdf.searchResults}
              clips={pdf.clips}
              thumbnails={pdf.thumbnails}
              onLoadThumbnail={pdf.loadThumbnail}
            />
          )}

          {activeView === "agents" && (
            <AgentPanel
              agents={agents.agents}
              loading={agents.loading}
              searchResults={agents.searchResults}
              onSearch={agents.search}
              onCreate={agents.createAgent}
              onSelectAgent={handleSelectAgent}
            />
          )}

          {activeView === "editor" && (
            <LegalEditor
              documents={pdf.documents}
              clips={pdf.clips}
              onDraft={handleDraft}
              onReport={handleReport}
              isLoading={chat.isLoading}
            />
          )}
        </main>
      </div>
    </div>
  );
}
