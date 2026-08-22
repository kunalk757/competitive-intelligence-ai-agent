import { INITIAL_COMPANIES } from "../src/data/companies";

const EXPECTED_NAMES = [
  "NVIDIA",
  "AMD",
  "Intel",
  "Microsoft",
  "Google",
  "Apple",
  "Amazon",
  "Meta",
  "OpenAI",
  "Anthropic",
  "Tesla",
  "Samsung",
  "Qualcomm",
  "TSMC",
  "Broadcom",
  "IBM",
  "Oracle",
  "Salesforce",
  "Adobe",
  "Cisco"
];

console.log("=== VERIFYING COMPANIES DATA ===");
console.log(`Total count: ${INITIAL_COMPANIES.length} (expected: 20)`);
if (INITIAL_COMPANIES.length !== 20) {
  console.error("FAIL: Length mismatch");
  process.exit(1);
}

const names = INITIAL_COMPANIES.map(c => c.name);
const missing = EXPECTED_NAMES.filter(name => !names.includes(name));
if (missing.length > 0) {
  console.error(`FAIL: Missing companies: ${missing.join(", ")}`);
  process.exit(1);
}
console.log("✓ All 20 requested companies are present.");

// Test search filter logic
function filterCompanies(query: string) {
  const q = query.trim().toLowerCase();
  if (!q) return INITIAL_COMPANIES;
  return INITIAL_COMPANIES.filter(c => c.name.toLowerCase().includes(q));
}

const nvdaMatch = filterCompanies("NVIDIA");
console.log(`Filter 'NVIDIA' -> ${nvdaMatch.length} match: ${nvdaMatch[0]?.name}`);
if (nvdaMatch.length !== 1 || nvdaMatch[0].name !== "NVIDIA") {
  console.error("FAIL: Search for NVIDIA failed");
  process.exit(1);
}

const appleMatch = filterCompanies("apple");
console.log(`Filter 'apple' -> ${appleMatch.length} match: ${appleMatch[0]?.name}`);
if (appleMatch.length !== 1 || appleMatch[0].name !== "Apple") {
  console.error("FAIL: Search for apple failed");
  process.exit(1);
}

console.log("=== ALL CHECKS PASSED ===");
