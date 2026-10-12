# Security and responsible use

This repository is research software. It is not a certified cryptographic
implementation, a constant-time proof, or a production security boundary.
Simulation checks cover specific inputs and operations. An accepted edit can
still contain an untested functional, timing, or side-channel defect.

## Keep sensitive material out of experiments

- Use public test vectors and synthetic keys, never production secrets.
- Model-backed runs may transmit RTL, timing reports, and prompts to an
  external provider. Check that you are permitted to share those inputs.
- Keep API keys and license configuration outside version control. Do not
  attach secrets or restricted PDK/library files to issue reports.
- Run proposed edits and EDA tools in a separate working tree or suitable
  sandbox. Review generated commands before using them in a privileged account.
- Keep the optional dashboard on a trusted local interface; it is a research
  log viewer, not an authenticated multi-user service.

## Report a problem

For a non-sensitive bug, report the checkout commit, minimal reproduction,
expected behavior, observed behavior, and sanitized logs through the
repository's normal contribution channel. Do not post a security-sensitive
exploit, secret, or proprietary design publicly. Use an available private
security-reporting channel or contact the repository maintainers privately
before disclosing sensitive details.

No response-time guarantee or dedicated security support is promised by this
research project.
