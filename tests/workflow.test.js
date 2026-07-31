import test from "node:test";
import assert from "node:assert/strict";
import { approveMatch, calculateMatchImpact, completeTask, createSyntheticMatch, suspendBatch } from "../src/workflow.js";

function state() {
  return {
    recipients: [{ id: "r1", status: "active", storage: ["dry"], evidenceCompliance: 1 }],
    animalGroups: [{ id: "g1", recipientId: "r1", species: "dog", count: 10, dailyCompleteFeedKg: 5 }],
    inventory: [{ id: "i1", animalGroupId: "g1", dietClass: "complete", quantityKg: 10 }],
    batches: [], matches: [], tasks: [], deliveries: [], feedingRecords: [], incidents: [], impactClaims: [], auditEvents: []
  };
}

test("synthetic batch can move through approval, tasks and impact", () => {
  const s = state();
  const { match } = createSyntheticMatch(s, { recipientId: "r1", animalGroupId: "g1", quantityKg: 20 });
  assert.equal(match.status, "pending_approval");

  const { tasks } = approveMatch(s, match.id);
  for (const task of tasks) completeTask(s, task.id, { synthetic: true });
  const impact = calculateMatchImpact(s, match.id);
  assert.equal(impact.claimStatus, "verified");
  assert.equal(impact.verifiedAnimalDays, 4);
});

test("incident suspension freezes batch and match", () => {
  const s = state();
  const { batch, match } = createSyntheticMatch(s, { recipientId: "r1", animalGroupId: "g1" });
  approveMatch(s, match.id);
  const incident = suspendBatch(s, batch.id, "Recall drill");
  assert.equal(incident.status, "open");
  assert.equal(s.batches[0].status, "suspended");
  assert.equal(s.matches[0].status, "suspended");
});
