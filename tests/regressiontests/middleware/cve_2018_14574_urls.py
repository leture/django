from django.conf.urls import patterns

urlpatterns = patterns('',
    # Accepts paths with two leading slashes.
    (r'^(.+)/security/$', 'view'),
)
