# AlphaForge Coding Standards

---

# Purpose

This document defines the coding standards for AlphaForge to ensure consistency, readability, maintainability, and long-term scalability.

---

# Python Standards

- Follow PEP 8 wherever practical.
- Use descriptive variable and function names.
- Prefer explicit code over implicit behaviour.
- Keep functions focused on a single responsibility.

---

# Naming Conventions

Modules

snake_case.py

Classes

PascalCase

Functions

snake_case

Variables

snake_case

Constants

UPPER_CASE

Private Members

_prefix_name

---

# Service Design

- One primary responsibility per service.
- Avoid duplicated business logic.
- Keep services independent whenever practical.
- Business logic belongs in services, not UI code.

---

# UI Standards

- UI components should only handle presentation and user interaction.
- Delegate investment logic to services.
- Reuse common UI components where appropriate.
- Use the shared theme definitions for colours and styling.

---

# Error Handling

- Validate external inputs.
- Raise meaningful exceptions where appropriate.
- Avoid silently ignoring errors.
- Log actionable diagnostic information.

---

# Testing Standards

- Add tests for all new investment engines.
- Update existing tests when behaviour changes.
- Keep tests deterministic and repeatable.

---

# Documentation

Every public module should include:

- Purpose
- Responsibilities
- Important assumptions (where applicable)

Complex algorithms should include concise explanatory comments.

---

# Git Standards

Before committing:

- Tests pass
- Documentation updated
- No unused code
- No commented-out legacy code
- Meaningful commit message

---

# Code Review Checklist

- Readable
- Tested
- Documented
- Modular
- No duplicated logic
- No unnecessary complexity

---

Owner

AlphaForge Engineering

Last Updated

Sprint 12.0.0
