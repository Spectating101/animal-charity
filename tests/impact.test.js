import test from "node:test";
import assert from "node:assert/strict";
import { calculateAnimalDays } from "../src/impact.js";

test("impact is blocked without evidence", () => {
  const result = calculateAnimalDays({ quantityKg: 100, dailyDemandKg: 25, verificationComplete: false });
  assert.equal(result.claimStatus, "blocked");
  assert.equal(result.verifiedAnimalDays, 0);
});

test("complete feed calculates coverage after verification", () => {
  const result = calculateAnimalDays({ quantityKg: 100, dailyDemandKg: 25, verificationComplete: true, dietClass: "complete" });
  assert.equal(result.claimStatus, "verified");
  assert.equal(result.verifiedAnimalDays, 4);
});

test("complementary feed is conservatively discounted", () => {
  const result = calculateAnimalDays({ quantityKg: 100, dailyDemandKg: 25, verificationComplete: true, dietClass: "complementary" });
  assert.equal(result.verifiedAnimalDays, 2);
});
