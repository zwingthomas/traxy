from google.cloud import secretmanager
import requests
import os

client = secretmanager.SecretManagerServiceClient()


def get_numeric_project_number():

    if os.getenv("GCP_PROJECT_NUMBER"):
        return os.getenv("GCP_PROJECT_NUMBER")

    METADATA_URL = "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id"
    HEADERS = {"Metadata-Flavor": "Google"}
    resp = requests.get(METADATA_URL, headers=HEADERS, timeout=2.0)
    resp.raise_for_status()
    return resp.text


def get_secret(secret_id: str) -> str:
    if os.getenv(secret_id):
        return os.getenv(secret_id)

    try:
        project_number = get_numeric_project_number()
    except:
        raise RuntimeError(
            f"Secret '{secret_id}' not found in env and not running on GCP."
        )

    name = f"projects/{project_number}/secrets/{secret_id}/versions/latest"
    return client.access_secret_version(name=name).payload.data.decode("UTF-8")
