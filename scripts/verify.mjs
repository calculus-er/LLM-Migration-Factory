/**
 * CI-friendly verification: backend smoke script, frontend lint+build, pytest.
 * Run from repo root: npm run verify
 * Requires: backend/venv with dependencies, Node/npm for frontend.
 */
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");

function pyExe() {
  return process.platform === "win32"
    ? path.join(root, "backend", "venv", "Scripts", "python.exe")
    : path.join(root, "backend", "venv", "bin", "python");
}

function run(cmd, args, cwd = root) {
  const r = spawnSync(cmd, args, { cwd, stdio: "inherit", shell: process.platform === "win32" });
  if (r.status !== 0) process.exit(r.status ?? 1);
}

const python = pyExe();
run(python, ["verify_backend.py"], root);
run("npm", ["run", "lint", "--prefix", "frontend"], root);
run("npm", ["run", "build", "--prefix", "frontend"], root);
run(python, ["-m", "pytest", "tests", "-q"], path.join(root, "backend"));

console.log("\n[OK] Full verify completed successfully.\n");
