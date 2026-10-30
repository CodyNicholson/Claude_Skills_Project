// Every lab demo in one place: what it teaches, how its request flows through the stack
// (drives the animated diagram), which buttons it has, and which call the "Run all" suite uses.
// Flow steps are [from, to, label]; from === to means work done inside that node.
// Replace the example below with one entry per __TOOL__ feature.

/** The participants a flow can show. Colors are CSS variables defined in App.css. */
export const NODE_META = {
  ui: { label: 'Browser', sub: 'React', color: 'var(--ui)' },
  api: { label: 'Backend', sub: 'lab API', color: 'var(--api)' },
  tool: { label: '__TOOL__', sub: 'the real thing', color: 'var(--accent)' },
  store: { label: 'Storage', sub: 'state / disk', color: 'var(--store)' },
};

/** Left-to-right order of the participants in every diagram. */
export const NODE_ORDER = ['ui', 'api', 'tool', 'store'];

export function nodesFor(flow) {
  const used = new Set(flow.flatMap(([from, to]) => [from, to]));
  return NODE_ORDER.filter((id) => used.has(id));
}

export const CATEGORIES = ['Basics'];

export const DEMOS = [
  {
    id: 'hello',
    category: 'Basics',
    title: 'Hello __TOOL__',
    tagline: 'The smallest possible round trip',
    description: [
      'Plain-language explanation of the feature: what problem it solves and the mental model behind it.',
      'What happens when you press the button, step by step, and what to look for in the visual below.',
      'A caveat, limit or production tip worth knowing.',
    ],
    keyApis: ['the main call()', 'an important option'],
    useCases: ['A real-world use', 'Another one'],
    snippet: { lang: 'text', code: '// The few lines of real code this demo runs on the backend' },
    inputs: [{ name: 'message', label: 'Message', type: 'text', default: 'hello' }],
    flow: [
      ['ui', 'api', 'POST /api/demos/hello'],
      ['api', 'tool', 'call the tool'],
      ['tool', 'tool', 'do the work'],
      ['tool', 'api', 'result'],
      ['api', 'ui', 'DemoResult + checks'],
    ],
    actions: [
      { id: 'run', label: 'Run it', method: 'POST', path: '/api/demos/hello', params: (i) => ({ message: i.message }), tone: 'accent' },
      { id: 'mistake', label: 'Do it wrong', method: 'POST', path: '/api/demos/hello', params: (i) => ({ message: i.message, mistake: true }), tone: 'ghost' },
    ],
    // Each pitfall: the mistake, the exact error or behaviour people see, why, how to fix it, how to
    // avoid it. Optional: wrongCode / rightCode (+ lang) side by side, and reproduce: an action id
    // that triggers the failure for real so visitors see the genuine error.
    pitfalls: [
      {
        mistake: 'The most common way people misuse this feature',
        symptom: 'The exact error message or wrong behaviour they see',
        why: 'What actually causes it',
        fix: 'How to resolve it once it has happened',
        avoid: 'The habit, setting or design that prevents it',
        lang: 'text',
        wrongCode: '// the code that causes it',
        rightCode: '// the corrected code',
        reproduce: 'mistake',
      },
    ],
    visual: 'hello',
    test: { method: 'POST', path: '/api/demos/hello?message=self-test' },
  },
];
