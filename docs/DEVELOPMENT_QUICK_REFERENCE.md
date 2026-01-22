# Kor'tana Development Quick Reference

## Overview

This guide provides quick access to key development resources for the Kor'tana project, linking together test strategies, expansion plans, and operational procedures.

**Last Updated:** January 22, 2026

---

## 🎯 Core Strategy Documents

### Test & Performance Matrix
**Document:** [`TEST_PERFORMANCE_MATRIX.md`](./TEST_PERFORMANCE_MATRIX.md)

**Purpose:** Comprehensive testing strategy and resource allocation for concurrent development.

**Key Sections:**
- Test coverage matrix (current: 51%, target: 90%)
- Performance benchmarks and targets
- Concurrent resource allocation across 4 development streams
- Quality gates and acceptance criteria
- Testing tools and infrastructure

**When to Use:**
- Planning test coverage improvements
- Allocating testing resources
- Setting performance targets
- Defining quality gates for releases

### Expansion Strategy Playbook
**Document:** [`EXPANSION_STRATEGY_PLAYBOOK.md`](./EXPANSION_STRATEGY_PLAYBOOK.md)

**Purpose:** Strategic roadmap for scaling Kor'tana through concurrent development.

**Key Sections:**
- 4 concurrent development streams (Core, Memory, API, Quality)
- Resource allocation guidelines
- 6-month timeline with milestones
- Risk management strategies
- Success metrics and KPIs

**When to Use:**
- Planning sprint goals
- Allocating team resources
- Tracking progress against milestones
- Making architectural decisions

---

## 🔄 Development Streams Overview

### Stream 1: Core Engine Enhancement
**Focus:** Brain system, Model Router, Response Generation  
**Team Size:** 2 developers  
**Test Coverage Target:** 85%+  
**Priority:** 🔴 Critical

**Key Components:**
- `src/kortana/brain.py` - ChatEngine
- `src/kortana/model_router.py` - SacredModelRouter
- `src/kortana/core/` - Core functionality

### Stream 2: Memory & Performance
**Focus:** Memory Manager, Database optimization, Caching  
**Team Size:** 2 developers  
**Test Coverage Target:** 90%+  
**Priority:** 🔴 Critical

**Key Components:**
- `src/kortana/memory/` - Memory system
- Database layer and optimization
- Redis caching implementation

### Stream 3: API & Integration
**Focus:** FastAPI endpoints, Authentication, External integrations  
**Team Size:** 1 developer  
**Test Coverage Target:** 80%+  
**Priority:** 🟡 High

**Key Components:**
- `src/kortana/api/` - API layer
- `src/kortana/llm_clients/` - LLM integrations
- Authentication and rate limiting

### Stream 4: Quality & Infrastructure
**Focus:** Testing, CI/CD, Monitoring, Documentation  
**Team Size:** 1 engineer  
**Test Coverage Target:** 100% automation  
**Priority:** 🟡 High

**Key Components:**
- `tests/` - Test suite
- CI/CD pipelines
- Monitoring and alerting
- Documentation

---

## 📊 Quick Metrics Dashboard

### Current State (January 2026)
```
Test Coverage:        51% ━━━━━━━━━━░░░░░░░░░ Target: 90%
Performance:          0.5s avg ━━━━━━░░░░ Target: 0.3s
Concurrent Users:     5 ━░░░░░░░░░░░░░░░░░░░ Target: 200
API Stability:        95% ━━━━━━━━━━━━━━░░ Target: 99.9%
```

### Key Targets by Quarter

**Q1 (Months 1-3):**
- ✅ 70% test coverage
- ✅ CI/CD pipeline operational
- ✅ 50 concurrent users supported
- ✅ <500ms API response (p95)

**Q2 (Months 4-6):**
- ✅ 90% test coverage
- ✅ 200 concurrent users supported
- ✅ <300ms API response (p95)
- ✅ 99.9% API availability

---

## 🧪 Testing Quick Reference

### Test Categories

| Type | Location | Count | Target | Command |
|------|----------|-------|--------|---------|
| Unit | `tests/unit/` | 9 | 40 | `pytest tests/unit/` |
| Integration | `tests/integration/` | 3 | 25 | `pytest tests/integration/` |
| E2E | `tests/` | 1 | 10 | `pytest tests/e2e.spec.ts` |
| Performance | TBD | 0 | 15 | `pytest --benchmark-only` |

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/kortana --cov-report=html

# Run specific stream tests
pytest tests/unit/core/  # Stream 1
pytest tests/unit/memory/  # Stream 2
pytest tests/integration/  # Stream 3

# Run performance benchmarks (when implemented)
pytest tests/performance/ --benchmark-only
```

### Quality Gates

**Pre-Commit:**
```bash
# Automated checks
black src/ tests/
ruff check src/ tests/
mypy src/
pytest tests/unit/
```

**Pre-Merge:**
```bash
# Full test suite
pytest tests/ --cov=src/kortana
pytest tests/integration/
# Performance check
pytest tests/performance/ --benchmark-compare
```

---

## 📚 Documentation Index

### Architecture & Design
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) - System architecture overview
- [`sacred_trinity_architecture.md`](./sacred_trinity_architecture.md) - Sacred Trinity design
- [`GOAL_FRAMEWORK_DESIGN.md`](./GOAL_FRAMEWORK_DESIGN.md) - Goal system design

### Development Guides
- [`GETTING_STARTED.md`](./GETTING_STARTED.md) - Initial setup guide
- [`TEST_PERFORMANCE_MATRIX.md`](./TEST_PERFORMANCE_MATRIX.md) - Testing strategy
- [`EXPANSION_STRATEGY_PLAYBOOK.md`](./EXPANSION_STRATEGY_PLAYBOOK.md) - Development roadmap

### API & Integration
- [`API_ENDPOINTS.md`](./API_ENDPOINTS.md) - API documentation
- [`LOBECHAT_CONNECTION.md`](./LOBECHAT_CONNECTION.md) - LobeChat integration
- [`LOBECHAT_TROUBLESHOOTING.md`](./LOBECHAT_TROUBLESHOOTING.md) - Troubleshooting

### Operations
- [`DATABASE_SCHEMA.md`](./DATABASE_SCHEMA.md) - Database schema
- [`ENHANCED_MONITORING_GUIDE.md`](./ENHANCED_MONITORING_GUIDE.md) - Monitoring setup
- [`AUTONOMOUS_SYSTEM_README.md`](./AUTONOMOUS_SYSTEM_README.md) - Autonomous features

---

## 🚀 Common Workflows

### Starting a New Feature

1. **Check the strategy:** Review relevant sections in `EXPANSION_STRATEGY_PLAYBOOK.md`
2. **Identify stream:** Determine which development stream (1-4)
3. **Check test matrix:** Review `TEST_PERFORMANCE_MATRIX.md` for testing requirements
4. **Create branch:** `git checkout -b stream-X/feature-name`
5. **Write tests first:** TDD approach (unit → integration → e2e)
6. **Implement feature:** Follow stream-specific guidelines
7. **Run quality gates:** Pre-commit checks
8. **Submit PR:** Include test coverage and performance impact

### Improving Test Coverage

1. **Check gaps:** Review coverage matrix in `TEST_PERFORMANCE_MATRIX.md`
2. **Prioritize:** Focus on critical components (Brain, Memory, Model Router)
3. **Write tests:** Follow testing pyramid (70% unit, 20% integration, 10% e2e)
4. **Run coverage:** `pytest --cov=src/kortana --cov-report=html`
5. **Update metrics:** Track progress against targets

### Performance Optimization

1. **Baseline:** Run performance benchmarks (see matrix)
2. **Profile:** Identify bottlenecks
3. **Optimize:** Make targeted improvements
4. **Benchmark:** Compare before/after
5. **Document:** Update performance metrics in matrix

---

## 📞 Getting Help

### Quick Links

- **Main README:** [`../README.md`](../README.md)
- **Project Map:** [`KORTANA_PROJECT_MAP.md`](./KORTANA_PROJECT_MAP.md)
- **Test Reporter:** `tests/test_reporter.py`
- **Issue Tracker:** GitHub Issues

### Team Contacts

- **Stream 1 Lead:** Core Engine questions
- **Stream 2 Lead:** Memory & Performance questions
- **Stream 3 Lead:** API & Integration questions
- **Stream 4 Lead:** Testing & Infrastructure questions

### When to Consult Which Document

| Question | Document |
|----------|----------|
| "What tests should I write?" | `TEST_PERFORMANCE_MATRIX.md` |
| "Which stream am I in?" | `EXPANSION_STRATEGY_PLAYBOOK.md` |
| "How does this component work?" | `ARCHITECTURE.md` |
| "What's the API endpoint?" | `API_ENDPOINTS.md` |
| "How do I set up my environment?" | `GETTING_STARTED.md` |
| "What's our roadmap?" | `EXPANSION_STRATEGY_PLAYBOOK.md` |

---

## 🎯 Next Steps

Based on your role and stream:

**Stream 1 (Core Engine):**
1. Review model router test coverage
2. Implement context optimization tests
3. Set up performance benchmarks

**Stream 2 (Memory & Performance):**
1. Set up Redis caching tests
2. Create database query benchmarks
3. Implement load testing framework

**Stream 3 (API & Integration):**
1. Complete API endpoint test coverage
2. Implement authentication tests
3. Create E2E workflow tests

**Stream 4 (Quality & Infrastructure):**
1. Configure CI/CD pipeline
2. Set up automated test reporting
3. Implement performance monitoring

---

**Document Version:** 1.0  
**Last Updated:** January 22, 2026  
**Maintained By:** Stream 4 (Quality & Infrastructure)

For updates or corrections, please submit a PR or contact the Stream 4 lead.
