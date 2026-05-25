import { expect, test, type Page } from "@playwright/test";

const sessionId = "session-stability-1";
const docId = "doc-ocr-1";

type MockState = {
  createSessionCalls: number;
  hasSession: boolean;
  hasDocument: boolean;
};

function message(id: string, role: "assistant" | "user" | "agent", content: string) {
  return {
    id,
    role,
    content,
    agent_id: role === "agent" ? "legal-chief" : undefined,
    agent_name: role === "agent" ? "@legal-chief" : undefined,
    timestamp: new Date().toISOString(),
    attachments: [],
    references: [],
    metadata: {},
  };
}

function documentMetadata() {
  return {
    doc_id: docId,
    filename: "BUSCA E APREENSÃO EM ALIENAÇÃO FIDUCIÁRIA (81).pdf",
    title: "Busca e apreensão",
    total_pages: 2,
    file_size_bytes: 1024,
    upload_timestamp: new Date().toISOString(),
    extracted_parties: [],
    process_number: "",
    court: "",
    subject: "",
    text_page_count: 0,
    scanned_page_count: 2,
    ocr_required: true,
    extraction_status: "ocr_required",
    extraction_warnings: [
      "2 de 2 pagina(s) parecem escaneadas e precisam de OCR.",
      "Nenhum texto selecionavel foi encontrado. A analise automatica fica limitada ate o OCR ser aplicado.",
    ],
  };
}

function sessionPayload(state: MockState) {
  return {
    session_id: sessionId,
    title: "Nova Analise",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    phase: "intake",
    messages: [
      message("welcome", "assistant", "Bem-vindo ao Legal Analyst Squad."),
      ...(state.hasDocument
        ? [
            message(
              "intake",
              "agent",
              "Documento recebido, mas a leitura automatica ainda esta incompleta.",
            ),
          ]
        : []),
    ],
    documents: state.hasDocument ? [documentMetadata()] : [],
    clips: [],
    active_agents: [],
    considerations: "",
    context_summary: "",
  };
}

async function installApiMocks(page: Page, state: MockState) {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (path === "/api/sessions" && method === "GET") {
      return route.fulfill({
        json: state.hasSession
          ? [{
              session_id: sessionId,
              title: "Nova Analise",
              phase: "intake",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              message_count: state.hasDocument ? 3 : 1,
              document_count: state.hasDocument ? 1 : 0,
            }]
          : [],
      });
    }

    if (path === "/api/sessions" && method === "POST") {
      state.createSessionCalls += 1;
      state.hasSession = true;
      return route.fulfill({ json: sessionPayload(state) });
    }

    if (path === `/api/sessions/${sessionId}` && method === "GET") {
      if (!state.hasSession) {
        return route.fulfill({ status: 404, json: { detail: "Sessao nao encontrada" } });
      }
      return route.fulfill({ json: sessionPayload(state) });
    }

    if (path === `/api/sessions/${sessionId}/pipelines/latest` && method === "GET") {
      return route.fulfill({ json: { pipeline: null } });
    }

    if (path === "/api/documents/upload" && method === "POST") {
      state.hasDocument = true;
      return route.fulfill({
        json: {
          doc_id: docId,
          filename: documentMetadata().filename,
          total_pages: 2,
          metadata: documentMetadata(),
        },
      });
    }

    if (path === "/api/chat" && method === "POST") {
      return route.fulfill({
        json: message(
          "agent-response",
          "agent",
          "Documento recebido, mas a leitura automatica ainda esta incompleta.",
        ),
      });
    }

    if (path === `/api/documents/${docId}/pages/1` && method === "GET") {
      return route.fulfill({
        json: {
          page_number: 1,
          text: "",
          images: [],
          word_count: 0,
          text_length: 0,
          image_count: 0,
          extraction_method: "ocr_unavailable",
          extraction_status: "ocr_required",
          needs_ocr: true,
        },
      });
    }

    if (path === `/api/documents/${docId}/pages/1/thumbnail` && method === "GET") {
      return route.fulfill({ status: 404, json: { detail: "Thumbnail nao disponivel" } });
    }

    return route.fulfill({ status: 404, json: { detail: `Unhandled mock route: ${method} ${path}` } });
  });
}

test("pt app route reuses analysis after reload and preserves scanned document state", async ({ page }) => {
  const state: MockState = {
    createSessionCalls: 0,
    hasSession: false,
    hasDocument: false,
  };
  await installApiMocks(page, state);

  await page.goto("/pt/app");
  await expect(page.getByRole("heading", { name: "Nenhuma analise ativa" })).toBeVisible();
  await expect(page.getByText("Transforme horas de trabalho")).toHaveCount(0);

  await page.getByRole("button", { name: "Nova analise" }).click();
  await expect(page.getByText("Bem-vindo ao Legal Analyst Squad.")).toBeVisible();
  expect(state.createSessionCalls).toBe(1);

  await page.setInputFiles("input[type=file]", {
    name: "BUSCA E APREENSÃO EM ALIENAÇÃO FIDUCIÁRIA (81).pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4\n% scanned placeholder\n"),
  });

  await expect(page.getByText("Documento precisa de leitura complementar")).toBeVisible();
  await expect(page.getByText("2 de 2 pagina(s) parecem escaneadas e precisam de OCR.").first()).toBeVisible();
  await expect(page.getByRole("button", { name: /Iniciar analise/ })).toBeDisabled();

  await page.reload();
  await expect(page.getByText("Documento precisa de leitura complementar")).toBeVisible();
  expect(state.createSessionCalls).toBe(1);

  await page.getByRole("button", { name: /Documentos/ }).click();
  await expect(page.getByText("BUSCA E APREENSÃO EM ALIENAÇÃO FIDUCIÁRIA (81).pdf").first()).toBeVisible();
});
