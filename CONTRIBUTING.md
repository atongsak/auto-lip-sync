# Artist-Driven Auto Lip Sync Blender Add-on
A Blender add-on that automates first-pass lip sync generation for pose-based character rigs using English audio.

## Overview
Thank you for your interest in contributing to this Blender add-on project! The project is currently in active development, and some components are still being implemented.

## Prerequisites & Local Setup
To develop the add-on locally, you'll need Blender 5.0+, Visual Studio Code, and a few development tools.

### 1. Clone the Repository
```
git clone https://github.com/atongsak/auto-lip-sync.git
cd auto-lip-sync
```
Open the repository in Visual Studio Code.

### 2. Install Visual Studio Code Tools
For the best development experience, install the following:
- [Blender Development](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development) by Jacques Lucke - allows you to run and debug Blender add-ons directly from VS Code.
- [fake-bpy-module](https://github.com/nutti/fake-bpy-module) - provides code completion and type hints for Blender's Python API.

If you're new to Blender add-on development, [this tutorial](https://youtu.be/YUytEtaVrrc?si=_HFTXqI2BWS0JTvu) by CG Python explains how to configure VS Code and use the Blender Development extension.

### 3. Install System Dependencies
Install the required system dependencies for your operating system by following the **Setup** section in the main README.

### 4. Launch the Add-on
Use the Blender Development extension to launch Blender from Visual Studio Code. The extension will install the add-on into Blender's development extensions directory, allowing you to iterate without manually packaging the add-on after every change.

## Running Quality Checks
At this time, there is no automated CI/CD pipeline configured. Quality is enforced through manual testing and verification prior to commits.

Before committing changes, contributors must:

* Ensure scripts execute without runtime errors
* Verify phoneme outputs are generated correctly
* Manually test Blender-related functionality
* Confirm no new dependency conflicts or warnings appear
* Review changes for clarity and consistency

## Contribution Workflow

### Branch Naming

Use descriptive branch names:

* `feature/phoneme-mapping`
* `feature/blender-api-integration`
* `fix/local-whisperx-bug`
* `docs/update-readme`

### Pull Requests

All changes should be submitted through a Pull Request (PR), which should include:

* A short summary of what was implemented or changed
* The related requirement ID(s), if applicable
* A description of how it was tested
* Screenshots or logs if relevant (especially for Blender functionality)

### Code Review Expectations

All PRs must be reviewed before merging.

As the primary contributor, the project maintainer performs a structured self-review prior to merge. Review includes:

* Verifying the implementation meets the stated requirement(s)
* Confirming no runtime errors are introduced
* Checking for unnecessary complexity or redundant code
* Ensuring consistency in naming, formatting, and structure
* Confirming that manual testing has been completed

If external contributors are added in the future, at least one approving review will be required before merging into the main branch.

### Definition of Done (DoD)

A contribution is considered complete when:

* Code runs without errors
* Core functionality works as expected in test cases
* Manual testing has been performed
* Documentation or notes have been updated if necessary

## Reporting Bugs / Requesting Changes

Please open a GitHub Issue for:

* Bug reports
* Feature requests
* Refactoring suggestions

Include:

* A clear description of the issue
* Steps to reproduce (if applicable)
* Expected vs. actual behavior
* Screenshots or error logs

## Where to Ask for Help

For questions about the project:

* Open a GitHub Issue for technical discussion
* Or contact the project maintainer directly via email (annettetongsak@gmail.com)
