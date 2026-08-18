# Taoyuan / Zhongli Sanmin Control-Plane Experiment

## Real public context

Taiwan MOA's `115年度遊蕩犬群優先管理指定區域` lists **Taoyuan City, Zhongli District, Sanmin Li (桃園市中壢區三民里)** as a **Level 1 public-safety-risk priority area**, where Level 1 is the highest risk tier in the designation methodology.

Official sources:

- programme: https://animal.moa.gov.tw/Frontend/News/Detail/N0000000002234
- priority-area PDF: https://animal.moa.gov.tw/public/upload/News/260316110439227006GR81L.pdf

The programme itself emphasizes systematic community management, priority risk areas, female-dog source control, NGO/community participation, responsible ownership and turning unmanaged feeding into responsible managed care.

### Critical boundary

That designation does **not** tell this repository:

- how many dogs are presently in Sanmin Li;
- which are owned, lost, abandoned or community-cared;
- which are sterilized;
- whether any current dog is sick, injured or dangerous;
- whether residents/owners/feeders have done anything wrong;
- whether foster/adoption capacity is currently constrained.

Therefore `examples/zhongli_sanmin_policy_baseline.json` contains **zero animal observations** and must produce **zero animal-level interventions**.

## Synthetic lifecycle gauntlet

`examples/zhongli_sanmin_synthetic_lifecycle.json` overlays fictional animals solely to test routing behaviour. It does not describe real Sanmin residents or animals.

The fixture contains:

1. a lost dog with verified/contactable owner -> reunification;
2. an owned dog at preventable relinquishment risk from a veterinary-cost shock -> owner-retention support;
3. three reproductively active free-roaming/community dogs -> source-control decisions and a repeated structural signal;
4. a placement-suitable dog with verified foster capacity -> foster-to-adoption route;
5. a medically stable/social/low-fear/low-reactivity dog that enjoys training -> **specialist referral only**, never automatic assignment;
6. an injured animal that also has a positive training signal -> emergency stabilization must preempt any specialist optimization.

## Expected structural insight

If three or more independently evidenced animals in one landscape repeatedly need the same source-control intervention, the area assessment may emit:

> Evaluate a targeted sterilization / registration / community-management initiative.

That is still not a launch order. The next structural layer must establish temporal recurrence, geographic/service coverage and operator capacity before proposing a pop-up/mobile/permanent programme.

## Why this experiment matters

The test is not whether an AI can invent an animal-welfare programme. It is whether the system can preserve the following ordering under pressure:

`acute welfare → prevent new unmanaged recruitment → keep safe homes intact → stable placement/community care → optional specialist role`

while refusing to infer individual facts from a high-risk-area label.
