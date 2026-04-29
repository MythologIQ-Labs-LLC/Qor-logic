// Gate enforcement policies for Qor-logic governance.
// Modelled after Cedar policy language (subset).

permit (
  principal,
  action == Action::"implement",
  resource == Gate::"plan"
) when { resource.verdict == "PASS" };

forbid (
  principal,
  action == Action::"implement",
  resource == Gate::"plan"
) when { resource.verdict == "VETO" };
