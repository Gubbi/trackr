import io
import json
import logging

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from lib.utils import google_api_access
from config import config


__author__ = 'vinuth'

_BUCKET_NAME = config.gs_bucket_name
_API_VERSION = 'v1'

google_auth, http = google_api_access('https://www.googleapis.com/auth/devstorage.read_write')


@google_auth
def get_resumable_upload_url(name, origin):
    return http.request('https://www.googleapis.com/upload/storage/v1/b/' +
                        _BUCKET_NAME + '/o?uploadType=resumable&name='+name, 'POST', headers={'Origin': origin})


@google_auth
def get_gcs_file(name):
    service = discovery.build('storage', _API_VERSION, http=http)
    req = service.objects().get_media(bucket=_BUCKET_NAME, object=name)
    resp = req.execute()
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, req, chunksize=1024*1024)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            logging.info('Download %d%%.' % int(status.progress() * 100))

    return fh.getvalue()


@google_auth
def delete_gcs_file(image_prop):
    service = discovery.build('storage', _API_VERSION, http=http)
    req = service.objects().delete(bucket=_BUCKET_NAME, object=image_prop.full_name)
    resp = req.execute()
    return json.dumps(resp, indent=2)


@google_auth
def list_gcs_files():
    service = discovery.build('storage', _API_VERSION, http=http)
    req = service.buckets().get(bucket=_BUCKET_NAME)
    resp = req.execute()
    return json.dumps(resp, indent=2)
