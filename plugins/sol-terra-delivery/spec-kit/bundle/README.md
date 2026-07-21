# Sol Terra Delivery Bundle

This manifest records the Spec Kit components installed by the toolkit installer:

- `sol-terra-artifacts` preset;
- `delivery-governance` extension;
- `sol-terra-pre-delivery` workflow.

The workflow ends after the second human approval. Runtime implementation is deliberately delegated to the Codex `$goal-driven-delivery` skill so Spec Kit and Codex do not compete for execution ownership.
