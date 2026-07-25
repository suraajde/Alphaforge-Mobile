# AlphaForge Development Rules

---

# Purpose

This document defines the engineering standards for developing AlphaForge.

Every contributor should follow these rules to maintain consistency, quality, and long-term maintainability.

---

# Project Structure

AlphaForge is organised into the following major components:

app/
Desktop UI (PySide6)

core/
Shared application utilities

services/
Business logic and investment engines

tests/
Automated tests

data/
Application data, cache, and universe files

docs/
Project documentation

launcher.py
Application entry point

---

# Layer Responsibilities

UI Layer

- Display information
- Handle user interaction
- Call services
- No investment logic

Service Layer

- Portfolio logic
- Research logic
- Scoring engines
- Decision engines
- Data processing

Core Layer

- Shared utilities
- Theme
- Version information
- Common application services

---

# Service Design Rules

Each service should have a single primary responsibility.

Services should remain independent whenever possible.

Avoid circular dependencies.

Business logic belongs in services, not UI classes.

---

# Naming Conventions

Services

*_service.py

Tests

test_*.py

Modules

snake_case

Classes

PascalCase

Functions

snake_case

Constants

UPPER_CASE

---

# Testing Rules

Every investment engine must have corresponding automated tests.

A sprint is not complete until:

- Implementation completed
- Tests passing
- Documentation updated
- Git commit created

Placeholder services should receive tests when implemented.

---

# Documentation Rules

Every completed sprint updates:

- 00_PROJECT_STATUS.md
- 02_CHANGELOG.md
- 09_VERSION_HISTORY.md

Update the roadmap whenever major milestones change.

---

# Git Workflow

1. Develop feature
2. Execute tests
3. Update documentation
4. Commit
5. Push

---

# Investment Principles

AlphaForge is designed for long-term investing.

Guiding principles include:

- Evidence-based decisions
- Explainable recommendations
- Low portfolio churn
- Configurable portfolio construction
- Risk-aware portfolio management

---

# Future Expansion

Future modules should integrate cleanly into the existing architecture without unnecessary restructuring.

---

Last Updated

Sprint 12.0.0
