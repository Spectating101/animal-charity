export function calculateAnimalDays({ quantityKg, dailyDemandKg, verificationComplete, dietClass = "complete" }) {
  if (!verificationComplete) {
    return {
      verifiedAnimalDays: 0,
      claimStatus: "blocked",
      reason: "Receipt and feeding evidence are incomplete."
    };
  }

  const quantity = Number(quantityKg);
  const demand = Number(dailyDemandKg);
  if (!Number.isFinite(quantity) || quantity <= 0 || !Number.isFinite(demand) || demand <= 0) {
    return {
      verifiedAnimalDays: 0,
      claimStatus: "blocked",
      reason: "Quantity and daily demand must be positive numbers."
    };
  }

  const coverageDays = quantity / demand;
  const multiplier = dietClass === "complete" ? 1 : dietClass === "complementary" ? 0.5 : 0.35;

  return {
    verifiedAnimalDays: Number((coverageDays * multiplier).toFixed(2)),
    claimStatus: "verified",
    reason:
      dietClass === "complete"
        ? "Complete-feed coverage calculated from verified use evidence."
        : `${dietClass} support is conservatively discounted and does not erase complete-feed stockout risk.`
  };
}
