# Optional OrbStack UI setup

OrbStack uses the same pinned Docker helper as Docker Desktop. Follow the
[current local development guide](docs/developer-guide/local-development.md).

```bash
./dev docker-start
# Open http://localhost:8123; use logs to check startup.
./dev docker-logs
./dev docker-stop
```

New containers use HA Core 2026.11.2 and a persistent
`my_verisure_dev_config` named volume. Starting/stopping no longer deletes the
container or its private storage. Existing containers retain their original
image/storage and need an intentional backed-up migration to adopt these flags.
The current audit validated helper commands with inert Docker stubs; it did not
start an OrbStack/Docker runtime. See [pinned offline tests](QUICKSTART.md) for
the executed verification path.
