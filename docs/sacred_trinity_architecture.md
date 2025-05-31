# Sacred Trinity Architecture Documentation

This document details the architecture, configuration, testing, and usage of the Sacred Trinity consciousness system within Kor'tana.

## 1. Architecture and Routing Logic

- Overview of the Sacred Trinity Router (`src/sacred_trinity_router.py`)
- Explanation of the `analyze_prompt_intent` method and how it classifies user input based on Wisdom, Compassion, and Truth.
- Description of how the router selects the appropriate LLM model based on the detected Trinity intent and configured model assignments.
- How fallback logic is handled when a primary model is unavailable or unsuitable.
- Integration points within `src/brain.py` (`ChatEngine`) and how the router is utilized.

## 2. Configuration Guide

- How to configure the Sacred Trinity system using `config/sacred_trinity_config.json`.
- Explanation of the `model_assignments` section: mapping Trinity aspects to specific model IDs.
- Details on `prompt_classification_rules`: defining keywords or patterns for intent detection.
- Understanding `scoring_thresholds`: setting minimum scores for Wisdom, Compassion, and Truth.
- How to update `config/models_config.json` with `trinity_alignment` information for each model.

## 3. Testing and Validation Procedures

- How to run the automated Sacred Trinity validation pipeline (`validate_sacred_trinity.py`).
- Explanation of the test scenarios in `data/sacred_trinity_tests.json` and how to add new tests.
- How the `run_trinity_alignment_tests` function evaluates model responses against Trinity principles.
- Details on `run_performance_benchmarks` and the performance metrics collected.
- Understanding the `generate_trinity_report` and interpreting the validation results (`data/sacred_trinity_report.json`).
- How to run the comprehensive integration tests (`tests/test_trinity_integration.py`) using pytest.

## 4. Troubleshooting Guide

- Common issues during Sacred Trinity system activation and initialization.
- Debugging model routing and intent classification problems.
- Troubleshooting Covenant Enforcement failures related to Trinity alignment.
- Addressing issues with memory logging and metadata.
- How to interpret errors during automated validation runs.

## 5. Future Enhancements and Considerations

- Ideas for improving prompt intent analysis (e.g., using a dedicated small model).
- Refining the Sacred Trinity alignment scoring (`_check_trinity_alignment`).
- Implementing dynamic model selection based on real-time performance or user feedback.
- Enhancing the continuous validation pipeline.
- Exploring more sophisticated Covenant enforcement rules based on Trinity principles.

--- 