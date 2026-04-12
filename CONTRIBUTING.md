# Artist-Driven Auto Lip Sync Blender Add-on
A Blender add-on that does a first pass of lip sync animation given input audio.

# Overview
Thank you for your interest in contributing to this Blender add-on project! This repository contains ongoing work to connect WhisperX-based phoneme extraction with viseme mapping and Blender-based facial animation.

The project is currently in active development, and some components (such as full Blender API integration) are still being implemented.

# Prerequisites & Local Setup
**1. Clone the repository:**

``git clone https://github.com/atongsak/auto-lip-sync.git
cd auto-lip-sync``

**2. Python Environment**

The audio-to-phoneme extraction pipeline is currently developed and tested in Google Colab.

At this stage of development, dependencies are installed directly within the Colab notebook for reproducibility during testing. No finalized local environment configuration is required yet.

The pipeline has been verified with the following versions:

* `torch==2.3.1+cu121`
* `torchvision==0.18.1+cu121`
* `torchaudio==2.3.1+cu121`

As the project matures, a stable `requirements.txt` and local development setup will be formalized.

**3. Blender Setup (In Progress)**

Blender API integration is currently under development.
Testing Blender functionality requires:

* Installing Blender (latest LTS recommended)
* Running the add-on script from the Scripting workspace

Full audio → phoneme → viseme → blendshape automation is still being integrated.

# Running Quality Checks
At this time, there is no automated CI/CD pipeline configured. Quality is enforced through manual testing and verification prior to commits.

Before committing changes, contributors must:

* Ensure scripts execute without runtime errors
* Verify phoneme outputs are generated correctly
* Manually test Blender-related functionality
* Confirm no new dependency conflicts or warnings appear
* Review changes for clarity and consistency

# Contribution Workflow

## Branch Naming

Use descriptive branch names:

* `feature/phoneme-mapping`
* `feature/blender-api-integration`
* `fix/local-whisperx-bug`
* `docs/update-readme`

## Pull Requests

All changes should be submitted through a Pull Request (PR), which should include:

* A short summary of what was implemented or changed
* The related requirement ID(s), if applicable
* A description of how it was tested
* Screenshots or logs if relevant (especially for Blender functionality)

## Code Review Expectations

All PRs must be reviewed before merging.

As the primary contributor, the project maintainer performs a structured self-review prior to merge. Review includes:

* Verifying the implementation meets the stated requirement(s)
* Confirming no runtime errors are introduced
* Checking for unnecessary complexity or redundant code
* Ensuring consistency in naming, formatting, and structure
* Confirming that manual testing has been completed

If external contributors are added in the future, at least one approving review will be required before merging into the main branch.

## Definition of Done (DoD)

A contribution is considered complete when:

* Code runs without errors
* Core functionality works as expected in test cases
* Manual testing has been performed
* Documentation or notes have been updated if necessary

# Reporting Bugs / Requesting Changes

Please open a GitHub Issue for:

* Bug reports
* Feature requests
* Refactoring suggestions

Include:

* A clear description of the issue
* Steps to reproduce (if applicable)
* Expected vs. actual behavior
* Screenshots or error logs

# Where to Ask for Help

For questions about the project:

* Open a GitHub Issue for technical discussion
* Or contact the project maintainer directly via email (annettetongsak@gmail.com)
