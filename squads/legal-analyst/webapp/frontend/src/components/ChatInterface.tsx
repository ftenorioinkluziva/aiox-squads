import { useCallback, useRef, useState } from "react";
import {
  Send,
  Paperclip,
  Upload,
  AtSign,
  FileText,
  Scissors,
  ChevronUp,
  Loader2,
  AlertCircle,
  X,
  PlayCircle,
  CheckCircle2,
  Circle,
  Database,
  Plus,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import MessageBubble from "./MessageBubble";
import type { ChatMessage, DocumentMetadata, DocumentReference, PipelineRun } from "../types";

interface ChatInterfaceProps {
  hasActiveSession: boolean;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  scrollRef: React.RefObject<HTMLDivElement | null>;
  onSendMessage: (
    content: string,
    considerations?: string,
    references?: DocumentReference[],
    targetAgent?: string,
  ) => void;
  onNewSession: () => void;
  onUploadPDF: (file: File) => void;
  onIntakeDataJud: (tribunalAlias: string, processNumber: string) => Promise<void>;
  onDismissError: () => void;
  onReferenceClick?: (docId: string, page?: number) => void;
  documentCount: number;
  documents: DocumentMetadata[];
  pipeline: PipelineRun | null;
  pipelineLoading: boolean;
  pipelineError: string | null;
  onStartPipeline: () => void;
}

export default function ChatInterface({
  hasActiveSession,
  messages,
  isLoading,
  error,
  scrollRef,
  onSendMessage,
  onNewSession,
  onUploadPDF,
  onIntakeDataJud,
  onDismissError,
  onReferenceClick,
  documentCount,
  documents,
  pipeline,
  pipelineLoading,
  pipelineError,
  onStartPipeline,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const [considerations, setConsiderations] = useState("");
  const [showConsiderations, setShowConsiderations] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const [showDataJud, setShowDataJud] = useState(false);
  const [dataJudTribunal, setDataJudTribunal] = useState("tjdft");
  const [dataJudProcess, setDataJudProcess] = useState("");
  const [dataJudLoading, setDataJudLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    if (!hasActiveSession || !input.trim() || isLoading) return;
    onSendMessage(input, considerations || undefined);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }, [hasActiveSession, input, considerations, isLoading, onSendMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
      if (e.key === "/" && input === "") {
        setShowCommands(true);
      }
    },
    [handleSend, input],
  );

  const handleInput = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
    if (e.target.value.startsWith("*")) {
      setShowCommands(true);
    } else {
      setShowCommands(false);
    }
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file && hasActiveSession) {
        onUploadPDF(file);
        e.target.value = "";
      }
    },
    [hasActiveSession, onUploadPDF],
  );

  const commands = [
    { cmd: "*intake", desc: "Iniciar analise de processo via PDF", icon: Upload },
    { cmd: "*datajud", desc: "Consultar processo pelo numero", icon: Database },
    { cmd: "*relatorio", desc: "Gerar relatorio estrategico", icon: FileText },
    { cmd: "*minutar", desc: "Elaborar peca processual", icon: FileText },
    { cmd: "*pesquisar", desc: "Pesquisar jurisprudencia", icon: FileText },
    { cmd: "*recortar", desc: "Recortar trecho do documento", icon: Scissors },
    { cmd: "*agentes", desc: "Ver agentes disponiveis", icon: AtSign },
  ];

  const filteredCommands = input.startsWith("*")
    ? commands.filter((c) => c.cmd.includes(input.toLowerCase()))
    : commands;
  const documentsWithWarnings = documents.filter(
    (doc) => doc.ocr_required || doc.extraction_warnings.length > 0,
  );
  const documentsBlockingAnalysis = documents.filter(
    (doc) => doc.ocr_required || ["ocr_required", "empty"].includes(doc.extraction_status),
  );
  const canStartPipeline =
    documentCount > 0 &&
    documentsBlockingAnalysis.length === 0 &&
    (!pipeline || ["completed", "failed", "blocked"].includes(pipeline.status));
  const activePipeline = pipeline && ["queued", "running"].includes(pipeline.status);
  const phases = pipeline
    ? Array.from(new Map(pipeline.steps.map((step) => [step.phase_id, step.phase_name])).entries())
    : [];

  const handleDataJudSubmit = useCallback(async () => {
    if (!dataJudProcess.trim() || dataJudLoading) return;
    setDataJudLoading(true);
    try {
      await onIntakeDataJud(dataJudTribunal.trim(), dataJudProcess.trim());
      setDataJudProcess("");
      setShowDataJud(false);
    } finally {
      setDataJudLoading(false);
    }
  }, [dataJudLoading, dataJudProcess, dataJudTribunal, onIntakeDataJud]);

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <AnimatePresence>
          {messages
            .filter((m) => m.role !== "system")
            .map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onReferenceClick={onReferenceClick}
              />
            ))}
        </AnimatePresence>

        {!hasActiveSession && (
          <div className="flex h-full min-h-[320px] items-center justify-center px-4">
            <div className="max-w-sm text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-white/5">
                <FileText className="h-6 w-6 text-gray-500" />
              </div>
              <h2 className="text-sm font-semibold text-gray-200">
                Nenhuma analise ativa
              </h2>
              <p className="mt-2 text-xs leading-5 text-gray-500">
                Crie uma analise para anexar documentos, consultar DataJud ou iniciar o pipeline.
              </p>
              <button
                type="button"
                onClick={onNewSession}
                className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand-600 px-3 py-2 text-xs font-medium text-white hover:bg-brand-700"
              >
                <Plus className="h-3.5 w-3.5" />
                Nova analise
              </button>
            </div>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-3 px-4 py-3"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-legal-gold to-legal-darkgold flex items-center justify-center">
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            </div>
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-legal-gold/50 rounded-full animate-pulse-dot" />
              <span
                className="w-2 h-2 bg-legal-gold/50 rounded-full animate-pulse-dot"
                style={{ animationDelay: "0.3s" }}
              />
              <span
                className="w-2 h-2 bg-legal-gold/50 rounded-full animate-pulse-dot"
                style={{ animationDelay: "0.6s" }}
              />
            </div>
            <span className="text-xs text-gray-500">Processando...</span>
          </motion.div>
        )}
      </div>

      {/* Pipeline progress */}
      <AnimatePresence>
        {(pipeline || documentCount > 0 || pipelineError) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mx-4 mb-2 px-3 py-3 rounded-lg bg-white/[0.03] border border-white/10"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="text-xs font-semibold text-gray-200">
                  Analise processual
                </div>
                <div className="text-[11px] text-gray-500 mt-0.5">
                  {pipeline
                    ? `Status: ${pipeline.status}`
                    : "Pronta para iniciar com os documentos anexados"}
                </div>
              </div>
              <button
                onClick={onStartPipeline}
                disabled={!hasActiveSession || !canStartPipeline || pipelineLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-brand-600 hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed text-xs text-white"
              >
                <PlayCircle className="w-3.5 h-3.5" />
                {pipelineLoading ? "Iniciando..." : "Iniciar analise"}
              </button>
            </div>

            {pipelineError && (
              <div className="mt-2 text-xs text-red-300">{pipelineError}</div>
            )}

            {pipeline?.error_message && (
              <div className="mt-2 text-xs text-amber-200">{pipeline.error_message}</div>
            )}

            {phases.length > 0 && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-3">
                {phases.map(([phaseId, phaseName]) => {
                  const phaseSteps = pipeline!.steps.filter((step) => step.phase_id === phaseId);
                  const complete = phaseSteps.every((step) => step.status === "completed");
                  const running = activePipeline && pipeline!.current_phase_id === phaseId;
                  return (
                    <div
                      key={phaseId}
                      className={`flex items-center gap-2 px-2 py-1.5 rounded-md border text-[11px] ${
                        running
                          ? "border-brand-400/40 bg-brand-500/10 text-brand-100"
                          : complete
                            ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-100"
                            : "border-white/10 bg-white/[0.02] text-gray-400"
                      }`}
                    >
                      {complete ? (
                        <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                      ) : (
                        <Circle className="w-3.5 h-3.5 shrink-0" />
                      )}
                      <span className="truncate">{phaseName}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Extraction status banner */}
      <AnimatePresence>
        {documentsWithWarnings.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mx-4 mb-2 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20"
          >
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-amber-300 shrink-0 mt-0.5" />
              <div className="min-w-0">
                <div className="text-xs text-amber-200 font-medium">
                  Documento precisa de leitura complementar
                </div>
                <div className="text-xs text-amber-100/70 mt-1">
                  {documentsWithWarnings[0].extraction_warnings[0] ||
                    "Algumas paginas parecem escaneadas e precisam de OCR antes da analise completa."}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error banner */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mx-4 mb-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2"
          >
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span className="text-xs text-red-300 flex-1">{error}</span>
            <button onClick={onDismissError}>
              <X className="w-3.5 h-3.5 text-red-400" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Command palette */}
      <AnimatePresence>
        {showCommands && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="mx-4 mb-2 glass-panel p-2"
          >
            <div className="text-[10px] text-gray-500 px-2 py-1 uppercase tracking-wider">
              Comandos
            </div>
            {filteredCommands.map(({ cmd, desc, icon: Icon }) => (
              <button
                key={cmd}
                onClick={() => {
                  setInput(cmd + " ");
                  setShowCommands(false);
                  textareaRef.current?.focus();
                }}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors text-left"
              >
                <Icon className="w-4 h-4 text-gray-500" />
                <div>
                  <span className="text-sm text-brand-300 font-mono">{cmd}</span>
                  <span className="text-xs text-gray-500 ml-2">{desc}</span>
                </div>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Considerations panel */}
      <AnimatePresence>
        {showConsiderations && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mx-4 mb-2"
          >
            <div className="glass-panel p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400 font-medium">
                  Consideracoes do Advogado
                </span>
                <button
                  onClick={() => setShowConsiderations(false)}
                  className="text-gray-500 hover:text-gray-300"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              <textarea
                value={considerations}
                onChange={(e) => setConsiderations(e.target.value)}
                placeholder="Adicione suas consideracoes, estrategia preferida, pontos de atencao..."
                className="input-field text-xs resize-none"
                rows={3}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* DataJud panel */}
      <AnimatePresence>
        {showDataJud && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mx-4 mb-2"
          >
            <div className="glass-panel p-3">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-gray-300 font-medium">
                  Consulta DataJud
                </span>
                <button
                  onClick={() => setShowDataJud(false)}
                  className="text-gray-500 hover:text-gray-300"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="grid grid-cols-[96px_1fr_auto] gap-2">
                <input
                  value={dataJudTribunal}
                  onChange={(e) => setDataJudTribunal(e.target.value)}
                  className="input-field text-xs"
                  placeholder="tjdft"
                />
                <input
                  value={dataJudProcess}
                  onChange={(e) => setDataJudProcess(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleDataJudSubmit();
                    }
                  }}
                  className="input-field text-xs"
                  placeholder="Numero do processo"
                />
                <button
                  onClick={handleDataJudSubmit}
                  disabled={!dataJudProcess.trim() || dataJudLoading}
                  className="inline-flex items-center gap-1.5 px-3 rounded-md bg-brand-600 hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed text-xs text-white"
                >
                  {dataJudLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Database className="w-3.5 h-3.5" />
                  )}
                  Consultar
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input area */}
      <div className="p-4 border-t border-white/5">
        <div className="glass-panel flex items-end gap-2 p-2">
          {/* Action buttons */}
          <div className="flex gap-1 pb-1">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={!hasActiveSession}
              className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-legal-gold transition-colors"
              title="Enviar PDF"
            >
              <Upload className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowDataJud(!showDataJud)}
              disabled={!hasActiveSession}
              className={`p-2 rounded-lg hover:bg-white/10 transition-colors ${
                showDataJud ? "text-brand-400" : "text-gray-400"
              }`}
              title="Consultar DataJud"
            >
              <Database className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowConsiderations(!showConsiderations)}
              className={`p-2 rounded-lg hover:bg-white/10 transition-colors ${
                showConsiderations || considerations
                  ? "text-brand-400"
                  : "text-gray-400"
              }`}
              title="Consideracoes"
            >
              <ChevronUp className="w-4 h-4" />
            </button>
          </div>

          {/* Text input */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={!hasActiveSession}
            placeholder={hasActiveSession ? "Digite sua mensagem ou use * para comandos..." : "Crie uma analise para iniciar..."}
            className="flex-1 bg-transparent text-sm text-gray-100 placeholder:text-gray-600
                       resize-none focus:outline-none py-2 max-h-40"
            rows={1}
          />

          {/* Document count indicator */}
          {documentCount > 0 && (
            <div className="pb-1">
              <span className="badge-gold text-[10px]">
                <Paperclip className="w-3 h-3 mr-1" />
                {documentCount} doc{documentCount > 1 ? "s" : ""}
              </span>
            </div>
          )}

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={!hasActiveSession || !input.trim() || isLoading}
            className="p-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white
                       transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed
                       active:scale-95 mb-0.5"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center justify-center mt-2 gap-4">
          <span className="text-[10px] text-gray-600">
            Shift+Enter para nova linha
          </span>
          <span className="text-[10px] text-gray-700">|</span>
          <span className="text-[10px] text-gray-600">
            * para comandos
          </span>
          <span className="text-[10px] text-gray-700">|</span>
          <span className="text-[10px] text-gray-600">
            @agente para direcionar
          </span>
        </div>
      </div>
    </div>
  );
}
