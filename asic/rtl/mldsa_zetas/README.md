# ML-DSA ASIC constant-ROM component

`dual_port_rom.v` is a separately tested, optional constant-table replacement for
the qualified ML-DSA ROM. It preserves the enabled one-cycle read interface and
the 256 pinned zeta values without relying on FPGA power-up RAM initialization.
The upstream file remains unchanged. Compile exactly one of the original and
derivative modules.

This component is not selected by the default export and does not make the
whole design ASIC-ready. RAM and control-state initialization still need a
complete implementation and new whole-core qualification.

See [component checks and exact semantics](../../../verification/asic_memory/README.md)
and [the recorded result](../../../docs/verification/asic-memory-components-2026-10-12.json).
