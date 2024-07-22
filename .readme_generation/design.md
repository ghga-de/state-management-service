API calls to the State Management Service are authenticated through a configured API Key.

For each technology, REST API endpoints will be exposed, prefixed as follows:

| **Technology Name** | **Prefix**  |
|---------------------|-------------|
| MongoDB             | `/documents/`|
| Apache Kafka        | `/events/`  |
| S3                  | `/objects/` |
| Vault               | `/secrets/` |

Branch isolation is achieved in shared state technologies by the use of prefixes in,
for example, database names.
The `db_prefix` and `topic_prefix` config values are used so the prefixes must only be
specified once. They are applied to database and topic names automatically throughout
the SMS instance, establishing another means to restrict access.
