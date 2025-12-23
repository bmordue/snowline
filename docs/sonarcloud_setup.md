# SonarCloud Setup Guide

This document describes how to complete the SonarCloud setup for the Snowline project.

## Overview

SonarCloud is configured in this repository to provide automated static code analysis. The configuration files are already in place, but you need to complete a few manual setup steps in SonarCloud and GitHub.

## Prerequisites

- Admin access to the `bmordue/snowline` GitHub repository
- A SonarCloud account (free for public repositories)

## Setup Steps

### 1. Create SonarCloud Account and Project

1. Go to [SonarCloud](https://sonarcloud.io) and sign in using your GitHub account
2. Click on the "+" icon in the top right → "Analyze new project"
3. Select the `bmordue/snowline` repository from the list
4. Follow the setup wizard to create the project

### 2. Generate SonarCloud Token

1. In SonarCloud, click on your profile icon → "My Account"
2. Go to "Security" tab
3. Generate a new token:
   - Name: `GitHub Actions - Snowline`
   - Type: User Token
   - Expiration: Choose an appropriate expiration period
4. **Copy the token** - you'll need it in the next step

### 3. Add GitHub Secret

1. Go to your GitHub repository: `https://github.com/bmordue/snowline`
2. Click on "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add a secret with:
   - Name: `SONAR_TOKEN`
   - Value: The token you copied from SonarCloud
5. Click "Add secret"

### 4. Verify Configuration

The repository already contains the necessary configuration files:

- `sonar-project.properties` - SonarCloud project configuration
- `.github/workflows/ci.yml` - GitHub Actions workflow with SonarCloud scan

**Important**: You may need to update the `sonar.organization` value in `sonar-project.properties` if your SonarCloud organization name differs from your GitHub username. To find your organization name:

1. Log in to SonarCloud
2. Click on your profile icon → "My Organizations"
3. Find the organization key (it's typically your GitHub username or organization name)
4. Update the `sonar.organization` value in `sonar-project.properties` if different

If the organization name is incorrect, the SonarCloud scan will fail with an authentication error.

### 5. Test the Integration

1. Push a commit or create a pull request
2. Go to the "Actions" tab in GitHub to see the workflow run
3. Check the SonarCloud dashboard at `https://sonarcloud.io/project/overview?id=bmordue_snowline`
4. Verify that the code analysis results appear

## Configuration Details

### Project Settings

The SonarCloud configuration includes:

- **Project Key**: `bmordue_snowline`
- **Organization**: `bmordue` (update if different)
- **Main Language**: Python 3.12
- **Source Directories**: `src/`, `main.py`
- **Test Directory**: `tests/`

### Quality Gates

SonarCloud will automatically apply the default quality gate. You can customize this in the SonarCloud project settings:

1. Go to your project in SonarCloud
2. Click "Project Settings" → "Quality Gate"
3. Select or create a custom quality gate

### Pull Request Analysis

SonarCloud will automatically analyze pull requests and post comments on issues found. This helps maintain code quality before merging.

## Troubleshooting

### Build Fails with "SONAR_TOKEN not found"

- Ensure you've added the `SONAR_TOKEN` secret in GitHub repository settings
- The secret name must be exactly `SONAR_TOKEN`

### Analysis Not Appearing in SonarCloud

- Verify the project key in `sonar-project.properties` matches your SonarCloud project
- Check that your SonarCloud organization name is correct
- Review the GitHub Actions workflow logs for errors

### Updating the Configuration

If you need to modify the SonarCloud configuration:

1. Edit `sonar-project.properties` in the repository root
2. Commit and push the changes
3. The next workflow run will use the updated configuration

## Additional Resources

- [SonarCloud Documentation](https://docs.sonarcloud.io/)
- [GitHub Actions for SonarCloud](https://docs.sonarcloud.io/advanced-setup/ci-based-analysis/github-actions-for-sonarcloud/)
- [Quality Gates Guide](https://docs.sonarcloud.io/concepts/quality-gates/)
- [Python Analysis Parameters](https://docs.sonarcloud.io/advanced-setup/languages/python/)
