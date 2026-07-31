import test from "node:test";
import assert from "node:assert/strict";
import { evaluateBatch, scoreEligibleMatch } from "../src/rules.js";

const recipient = { status: "active", storage: ["dry"] };
const group = { species: "dog" };
const validBatch = {
  synthetic: true,
  sourceType: "commercial_feed",
  identityVerified: true,
  species: "dog",
  storageRequired: "dry",
  lotNumber: "LOT-1",
  expiresAt: "2026-12-31",
  flags: []
};

test("eligible synthetic commercial feed passes hard gates but still requires approval", () => {
  const result = evaluateBatch(validBatch, recipient, group);
  assert.equal(result.eligible, true);
  assert.equal(result.requiresHumanApproval, true);
  assert.equal(result.trace.every((item) => item.status === "pass"), true);
});

test("anonymous leftovers are rejected", () => {
  const result = evaluateBatch({ ...validBatch, sourceType: "anonymous_household_leftovers" }, recipient, group);
  assert.equal(result.eligible, false);
  assert.equal(result.trace.some((item) => item.ruleId === "SOURCE-001" && item.status === "fail"), true);
});

test("recalled goods are rejected", () => {
  const result = evaluateBatch({ ...validBatch, flags: ["recalled"] }, recipient, group);
  assert.equal(result.eligible, false);
});

test("real-world batches are disabled", () => {
  const result = evaluateBatch({ ...validBatch, synthetic: false }, recipient, group);
  assert.equal(result.eligible, false);
});

test("match score stays within 0-100", () => {
  const score = scoreEligibleMatch({ daysUntilStockout: 2, nutritionalFit: 1, routeEfficiency: 0.8, spoilageRisk: 0.5, reliability: 0.9, fairness: 0.8 });
  assert.ok(score >= 0 && score <= 100);
});
