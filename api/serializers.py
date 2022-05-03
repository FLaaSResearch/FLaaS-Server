from rest_framework import serializers
from api.models import Project, Round, Device, DeviceStatusResponse


class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = '__all__'  # ['id', 'title', 'create_date']


class RoundSerializer(serializers.ModelSerializer):

    model = serializers.ReadOnlyField()
    dataset = serializers.ReadOnlyField()
    dataset_type = serializers.ReadOnlyField()
    training_mode = serializers.ReadOnlyField()
    number_of_apps = serializers.ReadOnlyField()

    class Meta:
        model = Round
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Device
        fields = '__all__'


class DeviceStatusResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeviceStatusResponse
        fields = '__all__'


# class SessionSerializer(serializers.Serializer):
#     title = serializers.CharField(max_length=30)
#     model = serializers.CharField(max_length=15)
#     date = serializers.DateTimeField()

#     def create(self, validated_data):
#         return Session.objects.create(validated_data)

#     def update(self, instance, validated_data):

#         instance.title = validated_data.get('title', instance.title)
#         instance.model = validated_data.get('model', instance.model)
#         instance.date = validated_data.get('date', instance.date)

#         instance.save()
#         return instance
