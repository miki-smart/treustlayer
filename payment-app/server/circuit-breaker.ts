import { config } from "./config";

let consecutiveFailures = 0;
let openUntil = 0;

export function isCircuitOpen(): boolean {
  return Date.now() < openUntil;
}

export function recordSuccess(): void {
  consecutiveFailures = 0;
  openUntil = 0;
}

export function recordFailure(): void {
  consecutiveFailures += 1;
  if (consecutiveFailures >= config.circuitFailureThreshold) {
    openUntil = Date.now() + config.circuitOpenSeconds * 1000;
  }
}

/** Force-open for tests */
export function resetCircuitBreaker(): void {
  consecutiveFailures = 0;
  openUntil = 0;
}

/** Test hook: set open state */
export function setCircuitOpenForMs(ms: number): void {
  openUntil = Date.now() + ms;
}
