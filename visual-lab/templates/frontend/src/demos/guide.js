// The overview page: what __TOOL__ is, how to start a project with it (typed out in an animated
// terminal), and an honest pros / cons / when-to-use comparison. antiPatterns and troubleshooting
// also feed the #pitfalls page, next to every demo's own pitfalls.

export const OVERVIEW = {
  title: '__TOOL__ in one page',
  intro: 'One or two paragraphs: what __TOOL__ is, the problem it solves, and the core mental model.',
  facts: [
    ['Version in this lab', 'x.y.z'],
    ['License', '…'],
    ['Written in', '…'],
  ],
  steps: [
    {
      title: 'Install',
      text: 'How to add __TOOL__ to a project.',
      commands: ['echo "install command here"'],
    },
    {
      title: 'First program',
      text: 'The minimal working example.',
      file: { name: 'main.ext', code: '// minimal example' },
    },
  ],
  pros: ['Strength'],
  cons: ['Weakness or trade-off'],
  whenToUse: ['Good fit when …'],
  whenNotToUse: ['Pick something else when …'],
  alternatives: [['Alternative', 'how it differs']],
  // How NOT to use __TOOL__: misuses of the tool as a whole (wrong job, wrong architecture).
  antiPatterns: [
    { dont: 'Using __TOOL__ for a job it is not built for', why: 'What goes wrong and when it shows up', instead: 'What to do or use instead' },
  ],
  // Errors people hit outside any single feature: install, connection, auth, config, version upgrades.
  troubleshooting: [
    {
      mistake: 'A common setup or configuration mistake',
      symptom: 'The exact error message as printed',
      why: 'The cause',
      fix: 'Commands or settings that resolve it',
      avoid: 'How to prevent it',
    },
  ],
};
