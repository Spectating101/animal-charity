import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { readState, resetState, writeState } from "./store.js";
import {
  approveMatch,
  calculateMatchImpact,
  completeTask,
  createSyntheticMatch,
  suspendBatch
} from "./workflow.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.resolve(__dirname, "../public");
const port = Number(process.env.PORT || 3000);

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml"
};

function sendJson(response, status, payload) {
  response.writeHead(status, { "content-type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(payload, null, 2));
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  if (chunks.length === 0) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function dashboard(state) {
  const currentInventoryKg = state.inventory.reduce((sum, item) => sum + Number(item.quantityKg || 0), 0);
  return {
    mode: state.mode,
    counts: {
      recipients: state.recipients.length,
      animalGroups: state.animalGroups.length,
      batches: state.batches.length,
      matches: state.matches.length,
      pendingApprovals: state.matches.filter((item) => item.status === "pending_approval").length,
      openIncidents: state.incidents.filter((item) => item.status === "open").length
    },
    currentInventoryKg,
    verifiedAnimalDays: state.impactClaims
      .filter((item) => item.claimStatus === "verified")
      .reduce((sum, item) => sum + item.verifiedAnimalDays, 0),
    recentMatches: [...state.matches].reverse().slice(0, 10),
    tasks: state.tasks,
    batches: state.batches,
    impacts: state.impactClaims,
    incidents: state.incidents,
    auditEvents: [...state.auditEvents].reverse().slice(0, 20)
  };
}

async function handleApi(request, response, url) {
  let state = await readState();

  if (request.method === "GET" && url.pathname === "/api/state") {
    return sendJson(response, 200, state);
  }

  if (request.method === "GET" && url.pathname === "/api/dashboard") {
    return sendJson(response, 200, dashboard(state));
  }

  if (request.method === "POST" && url.pathname === "/api/reset") {
    state = await resetState();
    return sendJson(response, 200, dashboard(state));
  }

  if (request.method === "POST" && url.pathname === "/api/matches") {
    const body = await readJson(request);
    const result = createSyntheticMatch(state, body);
    await writeState(state);
    return sendJson(response, 201, result);
  }

  const approve = url.pathname.match(/^\/api\/matches\/([^/]+)\/approve$/);
  if (request.method === "POST" && approve) {
    const result = approveMatch(state, approve[1]);
    await writeState(state);
    return sendJson(response, 200, result);
  }

  const impact = url.pathname.match(/^\/api\/matches\/([^/]+)\/impact$/);
  if (request.method === "POST" && impact) {
    const result = calculateMatchImpact(state, impact[1]);
    await writeState(state);
    return sendJson(response, 200, result);
  }

  const task = url.pathname.match(/^\/api\/tasks\/([^/]+)\/complete$/);
  if (request.method === "POST" && task) {
    const body = await readJson(request);
    const result = completeTask(state, task[1], body.evidence);
    await writeState(state);
    return sendJson(response, 200, result);
  }

  const suspend = url.pathname.match(/^\/api\/batches\/([^/]+)\/suspend$/);
  if (request.method === "POST" && suspend) {
    const body = await readJson(request);
    const result = suspendBatch(state, suspend[1], body.reason);
    await writeState(state);
    return sendJson(response, 200, result);
  }

  return sendJson(response, 404, { error: "API route not found." });
}

async function serveStatic(response, pathname) {
  const relative = pathname === "/" ? "index.html" : pathname.replace(/^\//, "");
  const filePath = path.resolve(publicDir, relative);
  if (!filePath.startsWith(publicDir)) {
    response.writeHead(403);
    return response.end("Forbidden");
  }

  try {
    const file = await readFile(filePath);
    response.writeHead(200, { "content-type": contentTypes[path.extname(filePath)] || "application/octet-stream" });
    response.end(file);
  } catch {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
}

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, `http://${request.headers.host || "localhost"}`);
  try {
    if (url.pathname.startsWith("/api/")) return await handleApi(request, response, url);
    return await serveStatic(response, url.pathname);
  } catch (error) {
    const status = error instanceof SyntaxError ? 400 : 422;
    return sendJson(response, status, { error: error.message });
  }
});

server.listen(port, () => {
  console.log(`Animal Feed Relief Network validation app running at http://localhost:${port}`);
});
