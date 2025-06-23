from google.cloud import secretmanager
import requests

client = secretmanager.SecretManagerServiceClient()


def get_numeric_project_number():
    METADATA_URL = "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id"
    HEADERS = {"Metadata-Flavor": "Google"}
    resp = requests.get(METADATA_URL, headers=HEADERS, timeout=2.0)
    resp.raise_for_status()
    return resp.text


def get_secret(secret_id: str) -> str:
    project_number = get_numeric_project_number()
    name = f"projects/{project_number}/secrets/{secret_id}/versions/latest"
    return client.access_secret_version(name=name).payload.data.decode("UTF-8")
