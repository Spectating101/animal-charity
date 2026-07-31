import { calculateAnimalDays } from "./impact.js";
import { evaluateBatch, scoreEligibleMatch } from "./rules.js";
import { audit } from "./store.js";

function requireEntity(collection, id, label) {
  const entity = collection.find((item) => item.id === id);
  if (!entity) throw new Error(`${label} ${id} was not found.`);
  return entity;
}

export function createSyntheticMatch(state, input) {
  const recipient = requireEntity(state.recipients, input.recipientId, "Recipient");
  const animalGroup = requireEntity(state.animalGroups, input.animalGroupId, "Animal group");

  const batch = {
    id: `batch-${crypto.randomUUID()}`,
    synthetic: true,
    sourceType: input.sourceType || "commercial_feed",
    supplierName: input.supplierName || "Synthetic Supplier",
    productName: input.productName || "Sealed Adult Dog Complete Feed",
    species: input.species || animalGroup.species,
    dietClass: input.dietClass || "complete",
    quantityKg: Number(input.quantityKg || 100),
    lotNumber: input.lotNumber || "SYN-LOT-001",
    expiresAt: input.expiresAt || "2026-12-31T00:00:00.000Z",
    storageRequired: input.storageRequired || "dry",
    identityVerified: input.identityVerified !== false,
    flags: input.flags || [],
    status: "submitted",
    createdAt: new Date().toISOString()
  };

  const evaluation = evaluateBatch(batch, recipient, animalGroup);
  batch.status = evaluation.eligible ? "awaiting_manual_approval" : "quarantined";
  state.batches.push(batch);

  const currentInventory = state.inventory
    .filter((item) => item.animalGroupId === animalGroup.id && item.dietClass === "complete")
    .reduce((sum, item) => sum + Number(item.quantityKg || 0), 0);
  const daysUntilStockout = currentInventory / animalGroup.dailyCompleteFeedKg;

  const match = {
    id: `match-${crypto.randomUUID()}`,
    batchId: batch.id,
    recipientId: recipient.id,
    animalGroupId: animalGroup.id,
    status: evaluation.eligible ? "pending_approval" : "rejected",
    score: evaluation.eligible
      ? scoreEligibleMatch({
          daysUntilStockout,
          nutritionalFit: batch.dietClass === "complete" ? 1 : 0.6,
          routeEfficiency: 0.8,
          spoilageRisk: 0.4,
          reliability: recipient.evidenceCompliance,
          fairness: 0.8
        })
      : 0,
    ruleTrace: evaluation.trace,
    ruleVersion: "synthetic-v0.1",
    summary: evaluation.summary,
    createdAt: new Date().toISOString()
  };
  state.matches.push(match);

  audit(state, {
    action: "batch.evaluated",
    entityType: "batch",
    entityId: batch.id,
    metadata: { matchId: match.id, eligible: evaluation.eligible }
  });

  return { batch, match };
}

export function approveMatch(state, matchId, actor = "synthetic-reviewer") {
  const match = requireEntity(state.matches, matchId, "Match");
  if (match.status !== "pending_approval") {
    throw new Error(`Match ${matchId} is not pending approval.`);
  }

  const batch = requireEntity(state.batches, match.batchId, "Batch");
  match.status = "approved";
  match.approvedBy = actor;
  match.approvedAt = new Date().toISOString();
  batch.status = "approved_for_synthetic_dispatch";

  const taskTemplates = [
    ["pickup", "Record pickup quantity and custody timestamp."],
    ["delivery", "Record delivery quantity and recipient acknowledgement."],
    ["feeding_evidence", "Record verified use by the intended animal group."]
  ];

  const tasks = taskTemplates.map(([type, instruction], index) => ({
    id: `task-${crypto.randomUUID()}`,
    matchId,
    type,
    instruction,
    status: "pending",
    sequence: index + 1,
    evidence: null
  }));
  state.tasks.push(...tasks);

  audit(state, {
    action: "match.approved",
    actor,
    entityType: "match",
    entityId: match.id,
    metadata: { taskIds: tasks.map((task) => task.id) }
  });

  return { match, tasks };
}

export function completeTask(state, taskId, evidence, actor = "synthetic-operator") {
  const task = requireEntity(state.tasks, taskId, "Task");
  if (task.status === "complete") return task;

  const siblings = state.tasks
    .filter((item) => item.matchId === task.matchId)
    .sort((a, b) => a.sequence - b.sequence);
  const previousIncomplete = siblings.find((item) => item.sequence < task.sequence && item.status !== "complete");
  if (previousIncomplete) {
    throw new Error(`Task ${previousIncomplete.id} must be completed first.`);
  }

  task.status = "complete";
  task.completedAt = new Date().toISOString();
  task.completedBy = actor;
  task.evidence = evidence || { note: "Synthetic evidence recorded." };

  audit(state, {
    action: "task.completed",
    actor,
    entityType: "task",
    entityId: task.id,
    metadata: { matchId: task.matchId }
  });

  return task;
}

export function calculateMatchImpact(state, matchId) {
  const match = requireEntity(state.matches, matchId, "Match");
  const batch = requireEntity(state.batches, match.batchId, "Batch");
  const animalGroup = requireEntity(state.animalGroups, match.animalGroupId, "Animal group");
  const tasks = state.tasks.filter((task) => task.matchId === matchId);
  const verificationComplete = tasks.length > 0 && tasks.every((task) => task.status === "complete");

  const impact = calculateAnimalDays({
    quantityKg: batch.quantityKg,
    dailyDemandKg: animalGroup.dailyCompleteFeedKg,
    verificationComplete,
    dietClass: batch.dietClass
  });

  const claim = {
    id: `impact-${crypto.randomUUID()}`,
    matchId,
    ...impact,
    animalCount: animalGroup.count,
    createdAt: new Date().toISOString()
  };

  state.impactClaims = state.impactClaims.filter((item) => item.matchId !== matchId);
  state.impactClaims.push(claim);

  audit(state, {
    action: "impact.calculated",
    entityType: "impactClaim",
    entityId: claim.id,
    metadata: { matchId, claimStatus: claim.claimStatus }
  });

  return claim;
}

export function suspendBatch(state, batchId, reason, actor = "synthetic-risk-reviewer") {
  const batch = requireEntity(state.batches, batchId, "Batch");
  batch.status = "suspended";
  const affectedMatches = state.matches.filter((match) => match.batchId === batchId);
  for (const match of affectedMatches) match.status = "suspended";

  const incident = {
    id: `incident-${crypto.randomUUID()}`,
    batchId,
    status: "open",
    reason: reason || "Synthetic incident drill",
    openedBy: actor,
    openedAt: new Date().toISOString()
  };
  state.incidents.push(incident);

  audit(state, {
    action: "batch.suspended",
    actor,
    entityType: "batch",
    entityId: batchId,
    metadata: { incidentId: incident.id, reason: incident.reason }
  });

  return incident;
}
