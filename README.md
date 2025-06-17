# Project Name

## Table of Contents

- [Project Name](#project-name)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Project Structure](#project-structure)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Configuration](#configuration)
    - [Module 1](#module-1)
    - [Module 2](#module-2)
    - [Testing](#testing)
    - [Quality Checks](#quality-checks)
  - [License](#license)

## Overview

Briefly describe the project, its purpose, and key features.

## Project Structure

```text
├── .github
├── src
├── tests
├── LICENSE
├── Makefile
├── pyproject.toml
├── README.md
├── uv.lock
```

## Prerequisites

- Python 3.12
- XXX

## Installation

1. Clone the repository:

   ```bash
   git clone XXX
   cd XXX
   ```

2. Create a virtual environment:

   ```bash
   uv venv
   ```

3. Activate the virtual environment:
   - On Windows:

     ```bash
     .venv\Scripts\activate
     ```

   - On Unix or MacOS:

     ```bash
     source .venv/bin/activate
     ```

4. Install the required packages:

   ```bash
   uv sync --all-groups --all-extra
   ```

5. Create a `.env` file in the root directory:

   ```bash
    cp .env.example .env
   ```

## Usage

### Configuration

Configure API keys, model names, and other settings by editing:

src/configs/settings.py
src/configs/config.yaml

### Module 1

(Add description or usage example)

### Module 2

(Add description or usage example)

### Testing

Run all tests:

```bash
make tests
```

### Quality Checks

Run all quality checks (lint, format, type check, clean):

```bash
make all
```

Individual Commands:

- Display all available commands:

    ```bash
    make help
    ```

- Check code formatting:

    ```bash
    make ruff-check
    ```

- Format code:

    ```bash
    make ruff-format
    ```

- Lint code:

    ```bash
    make ruff-lint
    ```

- Type check

    ```bash
    make mypy
  ```

- Clean cache and build files:

    ```bash
    make clean
    ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
