# Aether Superpower Specification (SPEC.md)

## Intent

Defines the architectural contract and operational boundaries for modular superpowers within the Aether Forge ecosystem.

## Standards

- **Hermeticity**: Executors must not rely on global state.
- **DIP**: Every skill must depend on the `AetherSuperpower` base interface.
- **Verification**: Every executor must have a corresponding test suite in `tests/`.
- **Sovereignty**: Credentials must be injected via `.env`, never hardcoded.

## Signature

Every executor must implement:
`async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]`
