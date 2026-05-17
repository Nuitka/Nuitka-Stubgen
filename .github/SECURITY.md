# Security Policy

## Supported Versions

Security fixes are considered for the current development branch. This project
does not currently publish separate maintained release branches.

## Reporting a Vulnerability

Please do not report suspected vulnerabilities in public issues.

Use GitHub private vulnerability reporting if it is enabled for this repository.
If it is not enabled, contact a project maintainer through an appropriate private
channel and include:

- a description of the vulnerability
- steps to reproduce it
- the affected version or commit
- any known workaround or mitigation

Maintainers will review reports and coordinate fixes as appropriate for the
impact and complexity of the issue.

## Scope

This project generates `.pyi` stubs from Python source and includes tooling for
creating a vendorable implementation. Security reports should focus on behavior
that creates a concrete risk for users or downstream projects, such as unsafe
file handling, unintended code execution, or dependency-related exposure.
