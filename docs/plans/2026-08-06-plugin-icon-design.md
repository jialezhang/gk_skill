# GK Engineering Plugin Icon Design

## Decision

Use a text-free geometric mark that remains recognizable in both the 16–24 px composer surface and
the larger plugin detail card. A hexagon represents a bounded engineering system. A connected path
ending in an upper-right arrow represents dependency-aware execution converging into verified
delivery.

The composer icon is a monochrome SVG using `currentColor`, so it follows the host theme. The light
logo uses the plugin brand blue `#315EFB` with a white route. The dark logo uses a lighter blue body
with a dark navy route to preserve contrast. All assets are SVG, have no external dependencies, and
contain no small text or decorative detail that would disappear at compact sizes.

## Rejected directions

- A `GK` monogram depends on typography and loses clarity at small sizes.
- A sun-and-planet pairing makes Sol–Terra literal but can read as weather or astronomy.
- A detailed workflow diagram communicates the product but is too dense for an icon.

## Validation

The plugin manifest must expose `brandColor`, `composerIcon`, `logo`, and `logoDark`; every referenced
asset must exist inside the plugin archive. Plugin ingestion validation and the full toolkit test
suite remain the acceptance gates.
