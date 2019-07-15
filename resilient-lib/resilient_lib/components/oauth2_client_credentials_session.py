# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.
import time
import logging
import requests

log = logging.getLogger(__name__)


class OAuth2ClientCredentialsSession(requests.Session):
    """
    Wrapper around requests.Session that receives authentication tokens through
    'client_credentials' type of OAuth2 grant, and adds tokens to the requests made through the session,
    as well as attempts to keep track of the token and refresh it when the time comes.

    If proxies are defined, every request will use them.
    This session doesn't requests authorization from the user first, the scope should be pre-authorized.

    Usage:
    >>> api1 = OAuth2ClientCredentialsSession('https://example1.com/{}/oauth/v2/', tenant_id='xxx',\
                        client_id='xxx', client_secret='xxx')
    >>> api2 = OAuth2ClientCredentialsSession('https://example2.com/{}/oauth/v2/', tenant_id='xxx',\
                        client_id='xxx', client_secret='xxx')
    >>>
    >>> api1.post('https://example1.com/v4/me/messages', data={}) # use as a regular requests session object
    >>> api2.get('https://example2.com/v2/me/updates')
    >>> # When writing an integration use RequestsCommon to get the proxies defined in options
    >>> rc = RequestsCommon(xxx)
    >>> api3 = OAuth2ClientCredentialsSession('https://example3.com/{}/test', proxies=rc.get_proxies())
    """

    AUTHORIZATION_ERROR_CODES = [401, 403]
    DEFAULT_TENANT_ID = "common"

    def __new__(cls, *args, **kwargs):
        """
        Creates a singleton per authorization url / API.
        This means that the same class can be used to access multiple OAuth2 APIs, and each API's session
        would be a separate singleton with their own managed tokens.

        Guido Van Rossum's Singleton, modified to hold objects in a dictionary
        with key being request URL, so that multiple CredentialSession could be created from the class.
        https://www.python.org/download/releases/2.2/descrintro/#__new__
        """
        url = kwargs.get('url')

        if not url and len(args) > 1:
            url = args[0]
        else:
            raise ValueError("url is not provided")

        # __it__ is a dictionary that stores session for each API
        # the key is authorization API, the value is the session
        if cls.__dict__.get("__it__", None) is None:
            cls.__it__ = {}
        dict_it = cls.__dict__.get("__it__", None)
        # if there's an entry in the dictionary for given API return it
        if dict_it.get(url, None) is not None:
            return dict_it[url]
        # create session and save it in the dictionary with url as key
        it = requests.Session.__new__(cls)
        dict_it[url] = it
        return it

    def __init__(self, url=None, tenant_id=None, client_id=None, client_secret=None, scope=None, proxies=None):
        """
        Get OAuth2 tokens and save them to be used in session requests.
        :param url: Pythonic template with authorization url where tenant_id gets inserted
        :param client_id: API key/User Id
        :param client_secret: secret for API
        :param scope: optional, list of scopes
        :param proxies: Dict - proxies to make the requests through
        """
        # __init__ is run even if __new__ returned existing instance
        if getattr(self, "authorization_url", None) is not None:
            return

        super(OAuth2ClientCredentialsSession, self).__init__()
        log.debug("Creating OAuth2 Session.")
        if url is None or client_id is None or client_secret is None:
            missing_fields = list()
            if not url:
                missing_fields.append("url")
            if not client_id:
                missing_fields.append("client_id")
            if not client_secret:
                missing_fields.append("client_secret")
            raise ValueError("Missing fields ({}) required for OAuth2 authentication."
                             .format(",".join(missing_fields)))

        if tenant_id is None:
            tenant_id = self.DEFAULT_TENANT_ID
            log.info("tenant_id wasn't provided, defaulting to '{}'.".format(self.DEFAULT_TENANT_ID))

        self.tenant_id = tenant_id
        self.authorization_url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope

        self.oauth_token_data = None
        self.expires_in = None
        self.access_token = None
        self.token_type = None
        self.expiration_time = None
        self.proxies = proxies

        if not self.authenticate(url, tenant_id, client_id, client_secret, scope, proxies):
            raise ValueError("Wrong credentials for OAuth2 authentication with {0}".format(url))

    def authenticate(self, url, tenant_id, client_id, client_secret, scope, proxies=None):
        """
        :param url: String - authorization url - end point for authentication
        :param tenant_id: String - will default to 'common' if not supplied
        :param client_id: String
        :param client_secret: String
        :param scope: list<String> - list of scopes the token should provide access to
        :param proxies: object with proxy data
        :return: True/False - was/wasn't able to authenticate.
        """
        token_url = self.get_token_url(url, tenant_id)

        log.debug("Requesting token from {0}".format(url))
        r = self.get_token(token_url, client_id, client_secret, scope, proxies)

        log.info("Response status code: {}".format(r.status_code))
        r.raise_for_status()

        self.oauth_token_data = r.json()
        log.debug("Received oauth token.")

        self.expires_in = self.oauth_token_data.get("expires_in", None)
        if self.expires_in is not None:
            self.expiration_time = time.time() + self.expires_in
        else:
            self.expiration_time = None

        self.access_token = self.oauth_token_data["access_token"]
        self.token_type = self.oauth_token_data.get("token_type", None)

        return True

    @staticmethod
    def get_token_url(url, tenant_id):
        """
        Puts together token_url from url's template and tenant_id.
        """
        return url.format(tenant_id)

    @staticmethod
    def get_token(token_url, client_id, client_secret, scope=None, proxies=None):
        """
        Override this method if there are any specific things that need to be changed.
        Such as Cloud Foundry asking grant_type to be 'password' and API key to be passed in 'password'.
        """
        post_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
        if scope is not None:
            post_data['scope'] = scope
        return requests.post(token_url, data=post_data, proxies=proxies)

    def update_token(self):
        """
        Institutes a request for a new access token.
        """
        if not self.authenticate(self.authorization_url, self.tenant_id, self.client_id,
                                 self.client_secret, self.scope, self.proxies):
            raise ValueError("Can't update the token, did the credentials for {0} change?"
                             .format(self.authorization_url))
        return True

    def request(self, method, url, *args, **kwargs):
        """Constructs a :class:`Request <Request>`, injects it with tokens, sends it.
        If the request fails, likely because it was made before token expired, but expired in the process - retry.
        Returns :class:`Response <Response>` object.
        """

        if self.expiration_time is not None:
            if self.expiration_time < time.time():
                self.update_token()

        headers = kwargs.pop("headers") if "headers" in kwargs else {}

        self.add_authorization_header(headers)
        with requests.Session() as s:
            resp = s.request(method, url, *args, headers=headers, **kwargs)

        if resp.status_code in self.AUTHORIZATION_ERROR_CODES:
            self.update_token()
            with requests.Session() as s:
                resp = s.request(method, url, *args, headers=headers, **kwargs)

        return resp

    def add_authorization_header(self, headers):
        """
        Create headers needed for authentication/authorization, overriding the default ones if needed.
        """
        headers["Authorization"] = "{} {}".format(self.token_type, self.access_token)
