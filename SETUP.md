Project set up instructions:

- **AWS Account:** An AWS account with the necessary credentials is required to be able to deploy the AWS CDK Stack. Additionally, make sure you install the AWS CDK CLI following these [instructions](https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html).

- **Kubernetes:** You need to install the Kubernetes CLI (kubectl) on your computer to interact with it. Follow the instructions of your operating system [here](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html).

- **K9s:** Provides a terminal UI to interact with your Kubernetes clusters. Although it is not strictly necessary to install it, it allows access to your Kubernetes cluster from an interactive UI, making it easy to navigate through it (you won’t regret installing it!). Follow the instructions of your operating system [here](https://github.com/derailed/k9s).

- **Guardrails:** Guardrails AI requires a configuration file for setup. You will need to obtain a free GUARDRAILS_API_KEY to install and use the agents. The quick start guide can be found [here](https://www.guardrailsai.com/docs/getting_started/quickstart) to help you get started with this configuration, but there are mainly 2 steps to perform. First, configure the config file by running this command and providing the GUARDRAILS_API_KEY:

  ```bash
  guardrails configure
  ```
  
  Then install the respective guardrails:
  
  ```bash
  guardrails hub install hub://guardrails/toxic_language
  guardrails hub install hub://guardrails/detect_jailbreak
  guardrails hub install hub://guardrails/secrets_present
  ```

- **Qdrant Vector Database:** To use the Qdrant vector database, you will need to create a free Qdrant account, set up a free cluster, and get the QDRANT_API_KEY and QDRANT_URL.

- **API Keys:** For this project, you would need additionally a GH_TOKEN,  LANGSMITH_API_KEY, and OPENAI_API_KEY. The GitHub token must have access to public repositories (required to fetch issues).

- **Environment Variables:** There are two environment files for managing configurations, one for development (`.env.dev`) and one for production (`.env.prod`). You must create both files. After deploying the AWS CDK infrastructure, you will need to adapt the production environment variables, primarily the PostgreSQL connection parameters (user, password, host), which will be securely stored as secrets in AWS Secrets Manager. An additional SECRET_NAME parameter must be added to the production file to be able to retrieve the secrets programmatically.

- **Makefile:** To streamline environment management, the Makefile is set up to allow running the same commands depending on the environment. The APP_ENV variable is used to specify whether you want to work with development or production environments. Below is an example of how to run commands for different environments:

  ```bash
  drop-tables: ## Drop all tables in the PostgreSQL database APP_ENV=$(APP_ENV) uv run src/database/drop_tables.py
  ```
  
  Example usage:
  
  ```bash
  make drop-tables APP_ENV=dev
  ```
