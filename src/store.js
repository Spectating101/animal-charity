import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const runtimeDir = path.join(rootDir, "runtime");
const runtimeFile = path.join(runtimeDir, "state.json");
const seedFile = path.join(rootDir, "data", "seed.json");

async function ensureRuntime() {
  await mkdir(runtimeDir, { recursive: true });
  try {
    await readFile(runtimeFile, "utf8");
  } catch {
    const seed = await readFile(seedFile, "utf8");
    await writeFile(runtimeFile, seed, "utf8");
  }
}

export async function readState() {
  await ensureRuntime();
  return JSON.parse(await readFile(runtimeFile, "utf8"));
}

export async function writeState(state) {
  await ensureRuntime();
  await writeFile(runtimeFile, JSON.stringify(state, null, 2), "utf8");
  return state;
}

export async function resetState() {
  await ensureRuntime();
  const seed = JSON.parse(await readFile(seedFile, "utf8"));
  await writeState(seed);
  return seed;
}

export function audit(state, { action, actor = "system", entityType, entityId, metadata = {} }) {
  state.auditEvents.push({
    id: `audit-${crypto.randomUUID()}`,
    action,
    actor,
    entityType,
    entityId,
    metadata,
    occurredAt: new Date().toISOString()
  });
}
