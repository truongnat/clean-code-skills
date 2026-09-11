/**
 * ESLint flat config for the clean-code standard (skill: clean-code).
 *
 * Philosophy: the formatter (Prettier) owns layout, ESLint owns *structure* -
 *   function length, parameter count, complexity, nesting, dead code. Nobody
 *   has to argue about those in code review again.
 *
 * Usage: copy this file into the repo, `npm i -D eslint typescript-eslint prettier`,
 * then run `npx eslint .` (or let lint-staged run it on commit).
 */
import js from "@eslint/js";
import tseslint from "typescript-eslint";

/** Shared thresholds - ratchet them; turning everything on at once yields 4,000 errors. */
const LIMITS = {
  maxLinesPerFunction: 40,
  maxParams: 3,
  maxComplexity: 10,
  maxDepth: 3,
  maxCallbacks: 3,
};

export default tseslint.config(
  {
    ignores: ["dist/**", "build/**", "coverage/**", "node_modules/**", "**/*.min.*", "**/*.d.ts"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: { "@typescript-eslint": tseslint.plugin },
    rules: {
      // --- 3. Functions: small, one job, few parameters -------------------------------------
      "max-lines-per-function": [
        "warn",
        { max: LIMITS.maxLinesPerFunction, skipBlankLines: true, skipComments: true, IIFEs: false },
      ],
      "max-params": ["warn", { max: LIMITS.maxParams }],
      complexity: ["warn", LIMITS.maxComplexity],
      "max-depth": ["warn", { max: LIMITS.maxDepth }],
      "max-statements": ["warn", 20],
      "no-nested-ternary": "error",

      // --- 2. Naming ---------------------------------------------------------------
      "no-restricted-syntax": [
        "error",
        {
          message: "No single-letter names outside loops. Name things by intent.",
          selector: "Identifier[parent.type!='VariableDeclarator'][name=/^[a-z]$/]",
        },
        {
          message: "No Data/Info/Manager/Util/Object names - they carry no meaning.",
          selector:
            "Identifier[name=/(Data|Info|Manager|Handler|Processor|Util|Utils|Object|Obj|Thing|Stuff|Foo|Bar)$/]",
        },
        {
          message: "No negated booleans (`isNotXxx`) - hard to read once you invert the condition.",
          selector: "Identifier[name=/^isNot[A-Z]/]",
        },
      ],
      "@typescript-eslint/naming-convention": [
        "warn",
        { selector: "variable", format: ["camelCase", "PascalCase", "UPPER_CASE"], leadingUnderscore: "allow" },
        { selector: "typeLike", format: ["PascalCase"] },
        { selector: "enumMember", format: ["PascalCase", "UPPER_CASE"] },
        { selector: "typeParameter", format: ["PascalCase"] },
      ],

      // --- 4. Comments & dead code ---------------------------------------------------
      "no-warning-comments": ["warn", { terms: ["todo", "fixme", "xxx", "hack", "@todo"], location: "anywhere" }],
      "no-trailing-spaces": "error",
      "capitalized-comments": "off",
      "spaced-comment": ["warn", "always", { markers: ["/", "!", "TODO:", "region"] }],

      // --- 7. Exception handling --------------------------------------------------------
      "no-empty": ["error", { allowEmptyCatch: false }],
      "no-useless-catch": "error",
      "require-atomic-updates": "error",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_", caughtErrors: "all" }],

      // --- 9. Cleanup before production ---------------------------------------------
      "no-console": ["warn", { allow: ["error"] }],
      "no-debugger": "error",
      "no-alert": "error",
      eqeqeq: ["error", "always", { null: "ignore" }],
      curly: ["error", "all"],
      "prefer-const": "error",
      "no-var": "error",
      "object-shorthand": "warn",
      "no-param-reassign": ["warn", { props: false }],
      "default-case-last": "error",
      "max-len": [
        "warn",
        { code: 120, ignoreComments: true, ignoreUrls: true, ignoreStrings: true, ignoreTemplateLiterals: true },
      ],
      "no-duplicate-imports": "error",
    },
  },
  {
    // Rules that need type information - enabled for TS/TSX files only.
    files: ["**/*.ts", "**/*.tsx", "**/*.mts", "**/*.cts"],
    languageOptions: {
      parserOptions: {
        projectService: { allowDefaultProject: ["*.ts", "*.tsx"] },
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/no-misused-promises": "error",
      "@typescript-eslint/only-throw-error": "warn",
      "@typescript-eslint/prefer-promise-reject-errors": "warn",
      "@typescript-eslint/no-unnecessary-type-assertion": "warn",
      "@typescript-eslint/consistent-type-imports": [
        "warn",
        { prefer: "type-imports", fixStyle: "inline-type-imports" },
      ],
      "@typescript-eslint/no-confusing-void-expression": ["warn", { ignoreArrowShorthand: true }],
      // Queries do not change state, commands do not return data (command-query separation)
      "no-return-assign": "error",
    },
  },
  {
    // Test files may be longer and take more parameters: clarity beats brevity.
    files: ["**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts", "**/tests/**"],
    rules: {
      "max-lines-per-function": "off",
      "no-restricted-syntax": "off",
      "max-params": "off",
      "@typescript-eslint/no-explicit-any": "off",
      "no-magic-numbers": "off",
    },
  },
);
