export const sampleBaseline = {
  latency_ms: 100.0,
  memory_mb: 256.0,
  runtime_s: 2.5,
  throughput_rps: 1000.0,
};

export const sampleCurrent = {
  latency_ms: 125.0,
  memory_mb: 260.0,
  runtime_s: 2.7,
  throughput_rps: 850.0,
};

export const sampleDirections = {
  latency_ms: "higher_is_worse",
  memory_mb: "higher_is_worse",
  runtime_s: "higher_is_worse",
  throughput_rps: "lower_is_worse",
};
