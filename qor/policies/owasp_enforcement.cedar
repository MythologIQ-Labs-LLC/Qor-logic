// OWASP Top 10 enforcement policies for Qor-logic governance.
// Phase 23: wired into /qor-audit tribunal OWASP pass.

// A03 Injection: forbid shell=True in subprocess calls
forbid (
  principal,
  action == Action::"commit",
  resource == Code::"production"
) when { resource.has_shell_true == true };

// A08 Software/Data Integrity: forbid unsafe deserialization
forbid (
  principal,
  action == Action::"commit",
  resource == Code::"production"
) when { resource.has_unsafe_deserialization == true };

// A04 Insecure Design: forbid fail-open error handling
forbid (
  principal,
  action == Action::"commit",
  resource == Code::"production"
) when { resource.has_fail_open_error == true };

// A05 Security Misconfiguration: forbid hardcoded secrets
forbid (
  principal,
  action == Action::"commit",
  resource == Code::"production"
) when { resource.has_hardcoded_secrets == true };

// LLM01 Prompt Injection (Phase 53): forbid governance markdown containing canary patterns
forbid (
  principal,
  action == Action::"commit",
  resource == Code::"governance"
) when { resource.has_prompt_injection_canary == true };
