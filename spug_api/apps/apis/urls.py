# Copyright: (c) OpenSpug Organization. https://github.com/openspug/spug
# Copyright: (c) <spug.dev@gmail.com>
# Released under the AGPL-3.0 License.
from django.urls import path

from apps.apis import config
from apps.apis import deploy

urlpatterns = [
    path('config/', config.get_configs),
    path('deploy/<int:app_id>/', deploy.auto_deploy)
]
