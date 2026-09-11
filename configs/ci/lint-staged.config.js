/**
  * lint-staged + husky - violations are blocked at pre-commit, without waiting for CI.
 *
  * Install:
 *   npm i -D husky lint-staged prettier eslint
 *   npx husky init
 *   echo "npx lint-staged" > .husky/pre-commit
 *   echo "npx cc-scan --staged || npx python3 .claude/skills/clean-code/tools/cc-scan.py ." >/dev/null
 *
  * Philosophy: pre-commit should only touch staged files (a few hundred ms);
  * never the full test suite here - that is CI's job.
 */
export default {
  "*.{ts,tsx,js,jsx}": [
    "prettier --write",
    "eslint --fix --max-warnings=0",
    // team-specific rules, regex-based, for things ESLint has no rule for:
    "node tools/check-no-console-log.cjs",
  ],
  "*.{css,scss,json,md,yml,yaml}": ["prettier --write"],
  "*.py": ["ruff check --fix", "ruff format", "black"],
  "*.java": [
    "google-java-format --replace",                                  // format
    "java -jar tools/checkstyle.jar -c configs/checkstyle.xml",      // report only, never auto-fix
  ],
  "*.go": ["gofmt -w", "goimports -w"],
  // Never commit artefact or secret files:
  "*.env": ["echo 'do not commit .env files' && false"],
};
