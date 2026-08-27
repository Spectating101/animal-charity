# Control-Plane API

## `POST /v1/welfare/assess`

Authenticated operator endpoint for the regional lifecycle router.

Input: `WelfareLandscape` containing:

- area identity;
- optional policy context;
- explicit animal-level observations;
- known service capabilities.

Output: `AreaControlAssessment` containing:

- evidence-bounded intervention decisions;
- repeated transition-failure counts;
- structural signals;
- missing evidence;
- a safe conclusion.

The endpoint does **not** authorize physical action. Capture/dispatch, ownership determination, diagnosis/treatment, sterilization, foster/adoption approval, community return, dangerousness decisions, specialist-program acceptance and irreversible welfare decisions remain human/professional/competent-authority actions.

Example in demo mode:

```bash
export AFRN_DEMO_MODE=1
fastapi dev app/main.py

curl -X POST http://127.0.0.1:8000/v1/welfare/assess \
  -H 'Content-Type: application/json' \
  -H 'X-Actor: demo-reviewer' \
  --data @examples/zhongli_sanmin_synthetic_lifecycle.json
```
