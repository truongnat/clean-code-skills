// dependency-cruiser — dependency rules for a JS/TS repo (the "real parser" version of arch-scan).
// Install: npm i -D dependency-cruiser
// Run:     npx dependency-cruiser src --config configs/architecture/.dependency-cruiser.cjs
module.exports = {
  forbidden: [
    {
      name: 'domain-no-framework',
      severity: 'error',
      comment: 'The domain must be testable without a web/db framework.',
      from: { path: '^src/domain' },
      to: { pathNot: '^src/domain|^[.]', dependencyTypesNot: ['type-only'],
            path: 'node_modules/(react|express|next|sequelize|typeorm|prisma|axios)' },
    },
    {
      name: 'no-upward-import',
      severity: 'error',
      comment: 'Inner layers must not import outer ones — invert with a port.',
      from: { path: '^src/(domain|application)/' },
      to: { path: '^src/(infrastructure|interface|api)/' },
    },
    {
      name: 'feature-public-api-only',
      severity: 'error',
      comment: 'Reach another feature through its index/api module, never into its internals.',
      from: { path: '^src/features/([^/]+)/' },
      to: { path: '^src/features/(?!$1)([^/]+)/(?!index\.|api\.|contracts\.)' },
    },
    {
      name: 'no-circular',
      severity: 'error',
      comment: 'A cycle between modules means no part can be tested or moved alone.',
      from: { pathNot: '\.spec\.|\.test\.' },
      to: { circular: true },
    },
    {
      name: 'orphan-module',
      severity: 'info',
      comment: 'Nothing imports this file — either it is dead or the design is missing a wire.',
      from: { orphan: true, pathNot: '(main|index|test|spec)\.[jt]sx?$|\.d\.ts$' },
      to: {},
    },
  ],
  options: {
    doNotFollow: { path: 'node_modules' },
    exclude: { path: '(dist|build|coverage|node_modules)' },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: 'tsconfig.json' },
    enhancedResolveOptions: { exportsFields: ['exports'], conditionNames: ['import', 'require', 'node', 'default'] },
    reporterOptions: { dot: { collapsePattern: '^(src|packages)/[^/]+/[^/]+' } },
  },
};
