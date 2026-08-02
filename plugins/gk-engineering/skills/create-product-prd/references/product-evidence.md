# Product Evidence Protocol

## Inspect only what affects product truth

Relevant evidence may include:

- current routes, screens, navigation, and visible states;
- API behavior that directly constrains the user journey;
- authoritative domain entities and lifecycle states;
- existing product docs and accepted decisions;
- analytics, incidents, support reports, or reproduction evidence;
- screenshots or recordings supplied by the user.

Do not turn code organization into product requirements. A component name, endpoint shape, framework, or database table is normally planning evidence, not PRD content.

## Claim labels

- `Observed`: verified in current product/code/runtime.
- `User-approved`: explicitly decided in discovery.
- `Assumed`: useful for drafting but not yet confirmed.
- `Open`: requires product decision.

Blocking requirements may not rest solely on an unlabeled assumption.

## Evidence sufficiency

Use direct current-state evidence for claims about existing behavior. Use user approval for desired behavior and trade-offs. Use technical planning—not the PRD—to resolve SDK, module, file, and implementation uncertainty.
