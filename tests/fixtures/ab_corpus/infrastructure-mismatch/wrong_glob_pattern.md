# SEEDED TEST DEFECT -- NOT EXECUTABLE -- Phase 39 A/B corpus (F2 resolution).
# Plan claim

The classifier reads `.qor/gates/<sid>/audit*.json` and iterates multiple audit artifacts per session.

# Reality

`gate_chain.write_gate_artifact` writes singleton `audit.json` (overwrites). The glob yields one file.
