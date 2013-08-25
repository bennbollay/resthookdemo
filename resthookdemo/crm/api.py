import json as simplejson

from django.core.serializers import json

from tastypie.authentication import Authentication, SessionAuthentication, MultiAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer

from rest_hooks.models import Hook
from resthookdemo.crm.models import Contact, Deal


class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return simplejson.dumps(data, cls=json.DjangoJSONEncoder,
                sort_keys=True, ensure_ascii=False, indent=self.json_indent)

class UserObjectsOnlyAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        return object_list.filter(user=bundle.request.user)

    def read_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

    def create_list(self, object_list, bundle):
        return object_list

    def create_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

    def update_list(self, object_list, bundle):
        return [obj for obj in object_list if obj.user == bundle.request.user]

    def update_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

    def delete_list(self, object_list, bundle):
        return [obj for obj in object_list if obj.user == bundle.request.user]

    def delete_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user


class ApiKeyAuthentication(Authentication):
    def _unauthorized(self):
        from tastypie.http import HttpUnauthorized
        return HttpUnauthorized()

    def is_authenticated(self, request, **kwargs):
        from tastypie.compat import AUTH_USER_MODEL
        from tastypie.models import ApiKey

        api_key_raw = request.GET.get('api_key', None)
        print api_key_raw

        try:
            api_key = ApiKey.objects.select_related(AUTH_USER_MODEL).get(key=api_key_raw)
        except (ApiKey.DoesNotExist, ApiKey.MultipleObjectsReturned):
            return self._unauthorized()

        request.user = api_key.user

        return True


class ContactResource(ModelResource):
    def obj_create(self, bundle, request=None, **kwargs):
        return super(ContactResource, self).obj_create(bundle,
                                                       request,
                                                       user=request.user)

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)

    class Meta:
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization = UserObjectsOnlyAuthorization()
        serializer = PrettyJSONSerializer()
        queryset = Contact.objects.all()
        resource_name = 'contacts'

class DealResource(ModelResource):
    def obj_create(self, bundle, request=None, **kwargs):
        return super(DealResource, self).obj_create(bundle,
                                                    request,
                                                    user=request.user)

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(contact__user=request.user)

    class Meta:
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization = UserObjectsOnlyAuthorization()
        serializer = PrettyJSONSerializer()
        queryset = Deal.objects.all()
        resource_name = 'deals'

class HookResource(ModelResource):
    def obj_create(self, bundle, request=None, **kwargs):
        return super(HookResource, self).obj_create(bundle,
                                                    request,
                                                    user=request.user)

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(user=request.user)

    class Meta:
        resource_name = 'hooks'
        queryset = Hook.objects.all()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        serializer = PrettyJSONSerializer()
        authorization = UserObjectsOnlyAuthorization()
        allowed_methods = ['get', 'post', 'delete']
        fields = ['event', 'target']
