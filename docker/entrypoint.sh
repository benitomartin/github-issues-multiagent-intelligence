#!/bin/bash
set -e

echo "Starting application entrypoint..."

# Function to check if a package is installed
is_package_installed() {
    local package_name=$1
    if uv pip show "$package_name" > /dev/null 2>&1; then
        echo "$package_name is already installed, skipping."
        return 0  # Installed
    else
        echo "$package_name is not installed, installing..."
        return 1  # Not installed
    fi
}

# Function to check if a Guardrails validator is installed
is_guardrail_installed() {
    local validator_path=$1
    if [ -d "$validator_path" ]; then
        echo "Validator at $validator_path is already installed, skipping."
        return 0  # Installed
    else
        echo "Validator at $validator_path is not installed, installing..."
        return 1  # Not installed
    fi
}

# Function to setup guardrails if API key is provided
setup_guardrails() {
    if [ -n "$GUARDRAILS_API_KEY" ]; then
        echo "Setting up Guardrails..."

        # Run Guardrails configuration (if necessary)
        echo "Configuring Guardrails..."
        uv run guardrails configure --token "$GUARDRAILS_API_KEY" --disable-metrics --enable-remote-inferencing
        echo "Guardrails configuration completed!"

        # Install each validator if not already installed
        is_guardrail_installed "/app/.venv/lib/python3.12/site-packages/guardrails/hub/guardrails/toxic_language" || uv run guardrails hub install hub://guardrails/toxic_language
        is_guardrail_installed "/app/.venv/lib/python3.12/site-packages/guardrails/hub/guardrails/detect_jailbreak" || uv run guardrails hub install hub://guardrails/detect_jailbreak
        is_guardrail_installed "/app/.venv/lib/python3.12/site-packages/guardrails/hub/guardrails/secrets_present" || uv run guardrails hub install hub://guardrails/secrets_present

        echo "Guardrails setup completed!"
    else
        echo "GUARDRAILS_API_KEY not provided, skipping guardrails setup."
    fi
}

# Install extra packages if they are not installed
install_extra_packages() {
    is_package_installed "detoxify" || uv add detoxify
}

# Install extra packages
install_extra_packages

# Run Guardrails setup
setup_guardrails

echo "Starting application with command: $@"

# Execute the main command
exec "$@"
