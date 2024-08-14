# Copyright 2021 - 2024 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains a class that interfaces between inbound requests and object storage."""

from hexkit.protocols.objstorage import ObjectStorageProtocol
from hexkit.providers.s3 import S3ObjectStorage

from sms.config import Config
from sms.ports.inbound.objects_handler import ObjectsHandlerPort


# TODO: Handle left-field errors such as connection problems
class ObjectsHandler(ObjectsHandlerPort):
    """Class for object storage management (S3)."""

    def __init__(self, *, config: Config, object_storage: S3ObjectStorage):
        self._config = config
        self._storage = object_storage

    async def does_object_exist(self, bucket_id: str, object_id: str) -> bool:
        """Check if an object exists in the specified bucket.

        Returns `False` if the bucket does not exist or the object is not in the bucket,
        otherwise `True`.

        Raises:
        - `InvalidBucketIdError`: When the bucket ID is invalid.
        - `InvalidObjectIdError`: When the object ID is invalid.
        """
        try:
            return await self._storage.does_object_exist(
                bucket_id=bucket_id, object_id=object_id
            )
        except ObjectStorageProtocol.BucketNotFoundError:
            return False
        except ObjectStorageProtocol.BucketIdValidationError as err:
            raise self.InvalidBucketIdError(bucket_id=bucket_id) from err
        except ObjectStorageProtocol.ObjectIdValidationError as err:
            raise self.InvalidObjectIdError(object_id=object_id) from err

    async def empty_bucket(self, bucket_id: str) -> None:
        """Delete all objects in the specified bucket.

        Raises:
        - `BucketNotFoundError`: When the bucket does not exist.
        - `InvalidBucketIdError`: When the bucket ID is invalid.
        - `ObjectNotFoundError`: When an object is unexpectedly absent.
        """
        # Get list of all objects in the bucket
        object_ids = await self.list_objects(bucket_id=bucket_id)

        # iterate and delete
        for object_id in object_ids:
            # State shouldn't change between list_objects() and here
            # if it does, something weird is going on and we should raise an error
            try:
                await self._storage.delete_object(
                    bucket_id=bucket_id, object_id=object_id
                )
            except ObjectStorageProtocol.ObjectNotFoundError as err:
                raise self.ObjectNotFoundError(
                    object_id=object_id, bucket_id=bucket_id
                ) from err

    async def list_objects(self, bucket_id: str) -> list[str]:
        """List all objects in the specified bucket.

        Returns a list of object IDs contained by the bucket.

        Raises:
        - `BucketNotFoundError`: When the bucket does not exist.
        - `InvalidBucketIdError`: When the bucket ID is invalid.
        """
        try:
            return await self._storage.list_all_object_ids(bucket_id=bucket_id)
        except ObjectStorageProtocol.BucketNotFoundError as err:
            raise self.BucketNotFoundError(bucket_id=bucket_id) from err
        except ObjectStorageProtocol.BucketIdValidationError as err:
            raise self.InvalidBucketIdError(bucket_id=bucket_id) from err
