const PROHIBITED_SOURCE_TYPES = new Set([
  "anonymous_household_leftovers",
  "buffet_plate_waste",
  "unknown_mixed_dish"
]);

const PROHIBITED_FLAGS = new Set([
  "mould",
  "recalled",
  "cooked_bones",
  "chemical_exposure",
  "unknown_temperature_history",
  "damaged_internal_packaging",
  "raw_meat"
]);

function decision(ruleId, status, message, details = {}) {
  return { ruleId, status, message, details };
}

export function evaluateBatch(batch, recipient, animalGroup) {
  const trace = [];

  if (!batch || !recipient || !animalGroup) {
    return {
      eligible: false,
      requiresHumanApproval: true,
      trace: [decision("INPUT-001", "fail", "Batch, recipient and animal group are required.")]
    };
  }

  trace.push(
    decision(
      "MODE-001",
      batch.synthetic === true ? "pass" : "fail",
      batch.synthetic === true
        ? "Synthetic validation batch confirmed."
        : "Real-world batches are disabled in this validation build."
    )
  );

  trace.push(
    decision(
      "RECIPIENT-001",
      recipient.status === "active" ? "pass" : "fail",
      `Recipient status is ${recipient.status}.`
    )
  );

  trace.push(
    decision(
      "IDENTITY-001",
      batch.identityVerified === true ? "pass" : "fail",
      batch.identityVerified === true
        ? "Batch identity and product information are present."
        : "Batch identity is incomplete or unverified."
    )
  );

  trace.push(
    decision(
      "SOURCE-001",
      !PROHIBITED_SOURCE_TYPES.has(batch.sourceType) ? "pass" : "fail",
      PROHIBITED_SOURCE_TYPES.has(batch.sourceType)
        ? `Source type ${batch.sourceType} is prohibited.`
        : `Source type ${batch.sourceType} is allowed for evaluation.`
    )
  );

  const flags = Array.isArray(batch.flags) ? batch.flags : [];
  const blockedFlags = flags.filter((flag) => PROHIBITED_FLAGS.has(flag));
  trace.push(
    decision(
      "SAFETY-001",
      blockedFlags.length === 0 ? "pass" : "fail",
      blockedFlags.length === 0
        ? "No automatic rejection flags were supplied."
        : `Automatic rejection flags: ${blockedFlags.join(", ")}.`,
      { blockedFlags }
    )
  );

  const speciesCompatible = !batch.species || batch.species === animalGroup.species;
  trace.push(
    decision(
      "SPECIES-001",
      speciesCompatible ? "pass" : "fail",
      speciesCompatible
        ? `Batch is compatible with ${animalGroup.species}.`
        : `Batch species ${batch.species} does not match ${animalGroup.species}.`
    )
  );

  const storageRequired = batch.storageRequired || "dry";
  const storageCompatible = recipient.storage.includes(storageRequired);
  trace.push(
    decision(
      "STORAGE-001",
      storageCompatible ? "pass" : "fail",
      storageCompatible
        ? `${storageRequired} storage is available.`
        : `${storageRequired} storage is not available.`
    )
  );

  const hasLot = Boolean(batch.lotNumber);
  const hasExpiry = Boolean(batch.expiresAt);
  trace.push(
    decision(
      "TRACE-001",
      hasLot && hasExpiry ? "pass" : "fail",
      hasLot && hasExpiry
        ? "Lot and expiry information are present."
        : "Lot number and expiry are mandatory."
    )
  );

  const hardFailures = trace.filter((item) => item.status === "fail");
  const eligible = hardFailures.length === 0;

  return {
    eligible,
    requiresHumanApproval: true,
    trace,
    summary: eligible
      ? "Eligible for manual review; no automatic approval is permitted."
      : `Rejected or quarantined by ${hardFailures.length} hard gate(s).`
  };
}

export function scoreEligibleMatch({ daysUntilStockout, nutritionalFit, routeEfficiency, spoilageRisk, reliability, fairness }) {
  const clamp = (value) => Math.max(0, Math.min(1, Number(value) || 0));
  const urgency = 1 - clamp(daysUntilStockout / 14);
  const score =
    urgency * 0.3 +
    clamp(nutritionalFit) * 0.25 +
    clamp(routeEfficiency) * 0.15 +
    clamp(spoilageRisk) * 0.1 +
    clamp(reliability) * 0.1 +
    clamp(fairness) * 0.1;

  return Number((score * 100).toFixed(2));
}
