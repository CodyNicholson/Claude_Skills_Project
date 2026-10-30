// The DemoResult contract every demo endpoint returns, and a recorder that builds it.

export class Demo {
  constructor(name) {
    this.name = name;
    this.commands = [];
    this.checks = [];
    this.data = {};
    this.started = performance.now();
  }

  command(text) {
    this.commands.push(text);
  }

  check(name, passed, detail = '') {
    this.checks.push({ name, passed: Boolean(passed), detail: String(detail) });
  }

  /**
   * Run a step that may fail on purpose (a pitfall demo) and record the real error it throws.
   * const { error } = await d.attempt('client.get(missingKey)', () => client.get(missingKey));
   */
  async attempt(command, fn) {
    this.command(command);
    try {
      return { value: await fn(), error: null };
    } catch (err) {
      const error = `${err.name}: ${err.message}`;
      this.command(`  -> ${error}`);
      return { value: null, error };
    }
  }

  result() {
    return {
      demo: this.name,
      commands: this.commands,
      data: this.data,
      checks: this.checks,
      elapsedMs: Math.round((performance.now() - this.started) * 100) / 100,
    };
  }
}

/** The site is public through the tunnel: bound every size, count and duration a visitor can pick. */
export const clamp = (value, low, high) => Math.max(low, Math.min(high, Number(value) || low));
