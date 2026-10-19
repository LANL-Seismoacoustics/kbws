# Access Control

KBWS currently uses **deployment-scoped access control**. It does not implement
in-application user authentication, JWT validation, OAuth, or FDSN `queryauth`
endpoints.

Deploy each KBWS instance only where its intended users can reach it: for example,
behind an institutional network boundary, VPN, firewall rule, or reverse proxy.
User identity and authentication, when required, are the responsibility of that
deployment infrastructure.

## Oracle service identity

Each KBWS deployment should use one least-privileged, read-only Oracle service
account. Oracle DBAs should grant only `SELECT` access to the configured KB Core
tables or, preferably, dedicated read-only views. Do not grant DML, DDL, DBA-like
roles, or access beyond the data the deployment is intended to serve.

Oracle Wallet/external-secret authentication is supported as a deployment choice,
but is not required. Local or self-managed deployments can use a normal
`database_url` for their own tables. KBWS relies on the configured SQLAlchemy
connection and does not parse Wallet files or manage database credentials itself.

## Waveform files

Dataselect reads waveform files from paths in `wfdisc`. Oracle table permissions
therefore do not by themselves restrict waveform access. Mount only the waveform
directories a deployment may serve, and make those mounts read-only where possible.

## Operational correlation

KBWS assigns each response an `X-Request-ID` header. Formatted error responses
also include the request ID in their body, so users can provide it to an operator
when reporting a problem. Request IDs provide operational correlation only; they
are not user authentication or audit identities.
