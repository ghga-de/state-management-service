This service is intended to aid testing of the GHGA Archive by providing a unified
API for managing state in infrastructure technologies such as MongoDB, S3, Apache Kafka,
and the Hashicorp Vault.

This service should **never** be deployed to production. It is *only* intended for use
in the Testing and Staging environments, where there is no access to real data.
Despite this, there should be a way to restrict which databases and collections can be
accessed with this service through configuration, and a simple API key (set in config)
that can be used to authenticate requests.
