from rest_framework import serializers

from licenses.models import License

class LicenseSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name="license-detail")

    class Meta:
        model = License
        fields = ('url', 'name', 'text')

