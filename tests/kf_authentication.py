import collections
import logging
import os

import requests
from urllib.parse import parse_qs

logging.basicConfig(level=logging.DEBUG)


def kubeflow_login(url, username=None, password=None):
    """Completes the dex/oidc login flow, returning the authservice_session cookie."""
    parsed_url = urlparse(url)
    url_base = f"{parsed_url.scheme}://{parsed_url.netloc}"

    data = {
        'login': username or os.getenv('KUBEFLOW_USERNAME', None),
        'password': password or os.getenv('KUBEFLOW_PASSWORD', None),
    }

    if not data['login'] or not data['password']:
        raise ValueError(
            "Missing login credentials - credentials must be passed or defined"
            " in KUBEFLOW_USERNAME/KUBEFLOW_PASSWORD environment variables."
        )

    # GET on url redirects us to the dex_login_url including state for this session
    response = requests.get(url, verify=False, allow_redirects=True)
    validate_response_status_code(response, [200], f"Failed to connect to url site '{url}'.")
    dex_login_url = response.url
    logging.debug(f"Redirected to dex_login_url of '{dex_login_url}'")

    # Log in, retrieving the redirection to the approval page
    response = requests.post(dex_login_url, data=data, verify=False, allow_redirects=False)
    validate_response_status_code(
        response, [303], f"Failed to log into dex - are your credentials correct?"
    )
    approval_endpoint = response.headers['location']
    dex_approval_url = url_base + approval_endpoint
    logging.debug(f"Logged in with dex_approval_url of '{dex_approval_url}")

    # Get the OIDC approval code and state
    response = requests.get(dex_approval_url, verify=False, allow_redirects=False)
    validate_response_status_code(
        response, [303], f"Failed to connect to dex_approval_url '{dex_approval_url}'."
    )
    authservice_endpoint = response.headers['location']
    authservice_url = url_base + authservice_endpoint
    logging.debug(f"Got authservice_url of '{authservice_url}'")

    # Access DEX OIDC path to generate session cookie
    response = requests.get(
        authservice_url,
        verify=False,
        allow_redirects=False,
    )
    validate_response_status_code(
        response, [302], f"Failed to connect to authservice_url '{authservice_url}'."
    )

    return response.cookies['authservice_session']


def validate_response_status_code(response, expected_codes: list, error_message: str = ""):
    """Validates the status code of a response, raising a ValueError with message"""
    if error_message:
        error_message += "  "
    if response.status_code not in expected_codes:
        raise ValueError(
            f"{error_message}"
            f"Got response {response.status_code}, expected one of {expected_codes}"
        )


# For testing:
if __name__ == "__main__":
    host = os.getenv("KUBEFLOW_HOST", "http://10.64.140.43.nip.io")
    # Infers username and password from KUBEFLOW_USERNAME, KUBEFLOW_PASSWORD
    authsession_cookie = kubeflow_login(host)
    print(authsession_cookie)
