# Code Signing Policy

## Overview

Windows binaries of markIT are signed using a certificate provided by [SignPath Foundation](https://signpath.org) to the [SignPath.io](https://signpath.io) platform.

## What is signed

- `markIT.exe` — the Windows executable included in every release

## How signing works

1. Every release is built automatically by GitHub Actions (see [`.github/workflows/build.yml`](../.github/workflows/build.yml))
2. The build produces an unsigned artifact
3. The artifact is submitted to SignPath.io for signing
4. Every signing request requires manual approval by the project maintainer before the certificate is applied
5. The signed binary is published as a GitHub Release artifact

## Certificate

The code signing certificate is issued by **SignPath Foundation** (https://signpath.org), a non-profit organization that provides free code signing for open-source projects. The certificate identifies the publisher as **markIT**.

## Team

| Role | Responsibility |
|---|---|
| Author / Approver | [@daonatea](https://github.com/daonatea) — reviews and approves every signing request |

Multi-factor authentication is enabled for all team members with access to the signing workflow.

## External contributions

Pull requests from external contributors are reviewed by the maintainer before merging. No external code is signed without maintainer approval.

## Verification

To verify the signature on a Windows binary:

1. Right-click `markIT.exe` → Properties → Digital Signatures tab
2. The signer should show **markIT** issued by SignPath Foundation

Or via PowerShell:

```powershell
Get-AuthenticodeSignature .\markIT.exe
```

## Contact

For questions about this policy, open an issue at https://github.com/daonatea/martkit/issues
