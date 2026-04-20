/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    /* ========== L0: components/ui — no app-layer imports ========== */
    {
      name: 'ui-no-foundation',
      severity: 'error',
      comment: 'L0 (components/ui) must not import from foundation (L1)',
      from: { path: '^src/components/ui/' },
      to: { path: '^src/foundation/' },
    },
    {
      name: 'ui-no-domains',
      severity: 'error',
      comment: 'L0 (components/ui) must not import from domains (L2)',
      from: { path: '^src/components/ui/' },
      to: { path: '^src/domains/' },
    },
    {
      name: 'ui-no-pages',
      severity: 'error',
      comment: 'L0 (components/ui) must not import from pages (L3)',
      from: { path: '^src/components/ui/' },
      to: { path: '^src/pages/' },
    },

    /* ========== L1: foundation — no upward imports ========== */
    {
      name: 'foundation-no-domains',
      severity: 'error',
      comment: 'L1 (foundation) must not import from domains (L2)',
      from: { path: '^src/foundation/' },
      to: { path: '^src/domains/' },
    },
    {
      name: 'foundation-no-pages',
      severity: 'error',
      comment: 'L1 (foundation) must not import from pages (L3)',
      from: { path: '^src/foundation/' },
      to: { path: '^src/pages/' },
    },

    /* ========== L2: domains — no upward or cross-domain imports ========== */
    {
      name: 'domains-no-pages',
      severity: 'error',
      comment: 'L2 (domains) must not import from pages (L3)',
      from: { path: '^src/domains/' },
      to: { path: '^src/pages/' },
    },
    {
      name: 'media-no-annotation',
      severity: 'error',
      comment: 'domains/media must not import from domains/annotation',
      from: { path: '^src/domains/media/' },
      to: { path: '^src/domains/annotation/' },
    },
    {
      name: 'media-no-review-export',
      severity: 'error',
      comment: 'domains/media must not import from domains/review_export',
      from: { path: '^src/domains/media/' },
      to: { path: '^src/domains/review_export/' },
    },
    {
      name: 'annotation-no-media',
      severity: 'error',
      comment: 'domains/annotation must not import from domains/media',
      from: { path: '^src/domains/annotation/' },
      to: { path: '^src/domains/media/' },
    },
    {
      name: 'annotation-no-review-export',
      severity: 'error',
      comment: 'domains/annotation must not import from domains/review_export',
      from: { path: '^src/domains/annotation/' },
      to: { path: '^src/domains/review_export/' },
    },
    {
      name: 'review-export-no-media',
      severity: 'error',
      comment: 'domains/review_export must not import from domains/media',
      from: { path: '^src/domains/review_export/' },
      to: { path: '^src/domains/media/' },
    },
    {
      name: 'review-export-no-annotation',
      severity: 'error',
      comment: 'domains/review_export must not import from domains/annotation',
      from: { path: '^src/domains/review_export/' },
      to: { path: '^src/domains/annotation/' },
    },

    /* ========== L3: pages — no page-to-page imports ========== */
    {
      name: 'no-page-to-page',
      severity: 'error',
      comment: 'A page must not import from another page file (except Layout)',
      from: { path: '^src/pages/(?!Layout).*Page\\.tsx$' },
      to: { path: '^src/pages/.*Page\\.tsx$' },
    },

    /* ========== Circular dependencies ========== */
    {
      name: 'no-circular',
      severity: 'error',
      comment: 'No circular dependencies allowed',
      from: {},
      to: { circular: true },
    },
  ],
  options: {
    doNotFollow: {
      path: 'node_modules',
    },
    tsPreCompilationDeps: true,
    tsConfig: {
      fileName: 'tsconfig.app.json',
    },
    enhancedResolveOptions: {
      exportsFields: ['exports'],
      conditionNames: ['import', 'require', 'node', 'default'],
    },
  },
};
