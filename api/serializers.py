from rest_framework import serializers
from django.core.validators import MaxValueValidator


class InputGetSerializer(serializers.Serializer):
    operations = [
        ('insert', 'insert'),
        ('update', 'update'),
        ('delete', 'delete'),
        ('fetch', 'fetch'),
    ]
    choose_data_type = ['real_data', 'testing_data', 'learning_data', 'deleted_data']

    coll_name = serializers.CharField(max_length=255, required=True)
    db_name = serializers.CharField(max_length=255, required=True)
    operation = serializers.ChoiceField(choices=operations, required=True)
    filters = serializers.JSONField(required=False)
    api_key = serializers.CharField(max_length=510, required=True)
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)
    payment = serializers.BooleanField(default=True, allow_null=True, required=False)
    data_type = serializers.ChoiceField(choices=choose_data_type, required=True)


class InputPostSerializer(serializers.Serializer):
    operations = [
        ('insert', 'insert'),
        ('update', 'update'),
        ('delete', 'delete'),
        ('fetch', 'fetch'),
    ]
    choose_data_type = ['real_data', 'testing_data', 'learning_data', 'deleted_data']
    
    api_key = serializers.CharField(max_length=510, required=True)
    coll_name = serializers.CharField(max_length=255, required=True)
    db_name = serializers.CharField(max_length=255, required=True)
    operation = serializers.ChoiceField(choices=operations, required=True)
    data = serializers.JSONField(required=True)
    # payment = serializers.BooleanField(default=True, allow_null=True, required=False)
    is_deleted = serializers.BooleanField(default=False)
    data_type = serializers.ChoiceField(choices=choose_data_type, required=True)


class InputPutSerializer(serializers.Serializer):
    choose_data_type = ['real_data', 'testing_data', 'learning_data', 'deleted_data']
    api_key = serializers.CharField(max_length=510, required=True)
    db_name = serializers.CharField(max_length=100)
    coll_name = serializers.CharField(max_length=100)
    operation = serializers.CharField(max_length=10)
    query = serializers.JSONField(required=False)
    update_data = serializers.JSONField(required=False)
    payment = serializers.BooleanField(default=True, allow_null=True, required=False)
    data_type = serializers.ChoiceField(choices=choose_data_type, required=True)


class InputDeleteSerializer(serializers.Serializer):
    choose_data_type = ['real_data', 'testing_data', 'learning_data', 'deleted_data']
    api_key = serializers.CharField(max_length=510)
    db_name = serializers.CharField(max_length=100)
    coll_name = serializers.CharField(max_length=100)
    operation = serializers.CharField(max_length=10)
    query = serializers.JSONField(required=False)
    data_type = serializers.ChoiceField(choices=choose_data_type, required=True)


class NotEmptyStringValidator:
    def __call__(self, value):
        if value == "":
            raise serializers.ValidationError("This field cannot be empty.")


class NoSpecialCharsValidator:
    def __call__(self, value):
        for char in value:
            if not char.isalnum() and char != ',' and char != '_': # Added '_' to allowed characters
                raise serializers.ValidationError("This field cannot contain special characters except commas and underscores.")


class NoSpacesValidator:
    def __call__(self, value):
        if ' ' in value.strip():
            raise serializers.ValidationError("This field cannot contain spaces.")


class AddCollectionPOSTSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=510)
    db_name = serializers.CharField(max_length=100)
    num_collections = serializers.CharField(max_length=100)
    coll_names = serializers.CharField(max_length=10000)


class GetCollectionsSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=510, required=True)
    db_name = serializers.CharField(max_length=100)
    payment = serializers.BooleanField(default=True, allow_null=True, required=False)


class AddDatabasePOSTSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=510, required=True)
    # username = serializers.CharField(max_length=100, required=True, validators=[NotEmptyStringValidator(), NoSpecialCharsValidator(), NoSpacesValidator()])
    db_name = serializers.CharField(max_length=100, required=True, validators=[NotEmptyStringValidator(), NoSpecialCharsValidator(), NoSpacesValidator()])
    num_collections = serializers.IntegerField(required=True, validators=[MaxValueValidator(10000)])
    num_documents = serializers.IntegerField(required=True, validators=[MaxValueValidator(10000)])
    num_fields = serializers.IntegerField(required=True, validators=[MaxValueValidator(10000)])
    field_labels = serializers.CharField(max_length=100, required=True, validators=[NotEmptyStringValidator(), NoSpecialCharsValidator(), NoSpacesValidator()])
    coll_names = serializers.CharField(max_length=100, required=True, validators=[NotEmptyStringValidator(), NoSpecialCharsValidator(), NoSpacesValidator()])
    region_id = serializers.CharField(max_length=510, default='')

    def validate_field_labels(self, value):
        labels = value.split(',')
        for label in labels:
            if not label.strip():
                raise serializers.ValidationError("Each field label must not be empty.")
        return labels

    def validate_coll_names(self, value):
        names = value.split(',')
        if not any(name.strip() for name in names):
            raise serializers.ValidationError("At least one name is required.")
        return names

