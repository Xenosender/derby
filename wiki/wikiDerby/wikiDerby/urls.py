# coding: utf-8
from django.urls import include, re_path
from django.contrib import admin

from wiki.urls import get_pattern as get_wiki_pattern
from django_nyt.urls import get_pattern as get_notify_pattern
from django.conf.urls.static import static
from .settings import base as settings

admin.autodiscover()

urlpatterns = [
    # Examples:
    #re_path(r'^$', include('wikiDerby.views.home', namespace='home')),
    # url(r'^blog/', include('blog.urls')),

    re_path(r'^admin/', admin.site.urls),
    re_path(r'^notify/', get_notify_pattern()),
    re_path(r'', get_wiki_pattern()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Following is the url configuration for django-wiki. It puts the wiki in / so
# it’s important that it is the last entry in urlpatterns. You can also put it
# in /wiki by putting '^wiki/' as the pattern.

#urlpatterns += patterns('',
#    url(r'^notify/', django_notify.url.get_pattern()),
#    
#)
