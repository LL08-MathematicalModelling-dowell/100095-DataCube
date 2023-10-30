from rest_framework import serializers


class InputGetSerializer(serializers.Serializer):
    operations = [
        ('insert', 'insert'),
        ('update', 'update'),
        ('delete', 'delete'),
        ('fetch', 'fetch'),
    ]

    coll_name = serializers.CharField(max_length=255, required=True)
    db_name = serializers.CharField(max_length=255, required=True)
    operation = serializers.ChoiceField(choices=operations, required=True)
    filters = serializers.JSONField(required=False)
    api_key = serializers.CharField(max_length=510, required=True)
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)


class InputPostSerializer(serializers.Serializer):
    operations = [
        ('insert', 'insert'),
        ('update', 'update'),
        ('delete', 'delete'),
        ('fetch', 'fetch'),
    ]
    api_key = serializers.CharField(max_length=510, required=True)
    coll_name = serializers.CharField(max_length=255, required=True)
    db_name = serializers.CharField(max_length=255, required=True)
    operation = serializers.ChoiceField(choices=operations, required=True)
    data = serializers.JSONField(required=True)


class InputPutSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=510, required=True)
    db_name = serializers.CharField(max_length=100)
    coll_name = serializers.CharField(max_length=100)
    operation = serializers.CharField(max_length=10)
    query = serializers.JSONField(required=False)
    update_data = serializers.JSONField(required=False)


class InputDeleteSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=510)
    db_name = serializers.CharField(max_length=100)
    coll_name = serializers.CharField(max_length=100)
    operation = serializers.CharField(max_length=10)
    query = serializers.DictField(required=False)


class AddCollectionPOSTSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=510)
    db_name = serializers.CharField(max_length=100)
    num_collections = serializers.CharField(max_length=100)
    coll_names = serializers.CharField(max_length=10000)
