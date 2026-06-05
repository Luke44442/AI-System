'use strict';

const { v4: uuidv4 } = require('uuid');
const { runMarketScout }       = require('../agents/market-scout');
const { runValidation }        = require('../agents/validation');
const { runStoreBuilder }      = require('../agents/store-builder');
const { runListingEngine }     = require('../agents/listing-engine');
const { runProductCreator }    = require('../agents/product-creator');
const { runGrowthEngine }      = require('../agents/growth-engine');
const { buildExecutionPackage }= require('../agents/execution-controller');

let _abortRequested = false;

function stopCycle() {
  _abortRequested = true;
}

function checkAbort() {
  if (_abortRequested) throw new Error('Cycle stopped by user');
}

async function runCycle({ emit, apiKey, opts = {} }) {
  _abortRequested = false;

  const cycleId = uuidv4();
  const mode = opts.mode ?? 'build';
  const focusNiche = opts.focusNiche ?? null;
  const startedAt = new Date().toISOString();

  emit('agent:status', {
    agent: 'orchestrator',
    label: 'Orchestrator',
    status: 'active',
    message: `Starting ${mode.toUpperCase()} cycle${focusNiche ? ` — niche: ${focusNiche}` : ''}`,
  });

  // ── STEP 1: Market Scout ──────────────────────────────────────────────────
  checkAbort();
  emit('agent:chunk', { agent: 'orchestrator', text: `\n🧠 CYCLE ${cycleId.slice(0, 8)} — MODE: ${mode.toUpperCase()}\n${'─'.repeat(40)}\n\n` });

  const opportunities = await runMarketScout({ emit, apiKey, focusNiche });

  if (mode === 'explore') {
    // Explore mode: just return opportunities
    return {
      id: cycleId,
      mode,
      focusNiche,
      startedAt,
      completedAt: new Date().toISOString(),
      status: 'complete',
      opportunities,
      validated: null,
      hero: null,
      blueprint: null,
      listings: [],
      productSpec: null,
      growthPlan: null,
      executionPackage: null,
      approvalItems: [],
      approvalStatus: 'none',
    };
  }

  // ── STEP 2: Validation ────────────────────────────────────────────────────
  checkAbort();
  const { validated, hero } = await runValidation({ emit, apiKey, opportunities });

  // ── STEP 3: Store Builder ─────────────────────────────────────────────────
  checkAbort();
  const blueprint = await runStoreBuilder({ emit, apiKey, opportunity: hero });

  if (mode === 'build') {
    // Build mode: stop before growth + execution
    return {
      id: cycleId,
      mode,
      focusNiche,
      startedAt,
      completedAt: new Date().toISOString(),
      status: 'complete',
      opportunities,
      validated,
      hero,
      blueprint,
      listings: [],
      productSpec: null,
      growthPlan: null,
      executionPackage: null,
      approvalItems: [],
      approvalStatus: 'none',
    };
  }

  // ── STEP 4: Listing Engine ────────────────────────────────────────────────
  checkAbort();
  const listings = await runListingEngine({ emit, apiKey, opportunity: hero, blueprint });

  // ── STEP 5: Product Creator ───────────────────────────────────────────────
  checkAbort();
  const productSpec = await runProductCreator({ emit, apiKey, opportunity: hero, blueprint, listings });

  // ── STEP 6: Growth Engine ─────────────────────────────────────────────────
  checkAbort();
  const growthPlan = await runGrowthEngine({ emit, apiKey, opportunity: hero, blueprint, listings });

  // ── STEP 7: Execution Package (no AI — pure logic) ────────────────────────
  checkAbort();
  emit('agent:status', {
    agent: 'orchestrator',
    label: 'Orchestrator',
    status: 'packaging',
    message: 'Assembling execution package...',
  });

  const executionPackage = buildExecutionPackage({ opportunity: hero, blueprint, listings, productSpec, growthPlan });

  emit('agent:status', {
    agent: 'orchestrator',
    label: 'Orchestrator',
    status: 'complete',
    message: '✅ READY FOR APPROVAL — Review execution package',
  });

  return {
    id: cycleId,
    mode,
    focusNiche,
    startedAt,
    completedAt: new Date().toISOString(),
    status: 'complete',
    opportunities,
    validated,
    hero,
    blueprint,
    listings,
    productSpec,
    growthPlan,
    executionPackage,
    approvalItems: executionPackage.approvalItems,
    approvalStatus: 'pending',
  };
}

module.exports = { runCycle, stopCycle };
