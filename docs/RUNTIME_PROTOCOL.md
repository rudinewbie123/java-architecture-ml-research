# Runtime benchmark protocol

This workflow does not yet execute runtime benchmarks.

1. Only benchmark repositories whose pinned commit passes build, tests, startup, and health checks.
2. Define equivalent business operations across applications: same semantics, payload, data volume, authentication, DB seed, and response validation.
3. Record workload ID, environment ID, run ID, commit SHA, offered rate, duration, threads, connections, timestamps, errors/timeouts, raw latency histogram, server CPU/RSS, and load-generator CPU/RSS.
4. Use fixed-rate wrk2 latency tests and separate throughput tests where needed. Do not label generic wrk2 results as Barista results.
5. Warm up before measurement; conduct at least five valid repetitions per workload/load level, randomize run order, and retain raw outputs.
6. Barista is reserved for benchmark applications it supports; arbitrary repositories require application-specific workloads.
7. Keep results from different machines, JDKs, workloads, and data states in separate strata unless a controlled design justifies pooling.
